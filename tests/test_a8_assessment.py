import json
from unittest.mock import MagicMock
import pytest
from agent_core import a8_assessment as a8
from agent_core.a8_benchmark import score


def test_scope_has_18_unique_technical_controls():
    controls=a8.catalog()
    assert len(controls)==18
    assert len({c['control_id'] for c in controls})==18
    assert all(c['control_id'].startswith('A.8.') for c in controls)


@pytest.mark.parametrize('profile,expected',[('conforming','Compliant'),('mixed','Partially Compliant'),('nonconforming','Non-Compliant'),('incomplete','Insufficient Evidence')])
def test_baseline_against_designer_labels(profile,expected):
    report=a8.run(profile,'rules')
    assert len(report['records'])==18
    assert all(r['status']==expected for r in report['records'])
    assert all(r['evidence_ids']==[r['evidence']['evidence_id']] for r in report['records'])


def test_collector_hash_and_input_allowlist():
    c=a8.catalog()[0];e=a8.collect('mixed',c)
    assert len(e['source_sha256'])==64
    assert set(e['facts'])==set(c['checks'])
    assert 'expected' not in json.dumps(e)
    with pytest.raises(ValueError):a8.collect('../../reference',c)


def test_no_human_labels_means_no_human_accuracy():
    report=a8.run('mixed','rules');s=score([report],[])
    assert all(c['accuracy'] is None and c['rated']==0 for c in s['per_control'])


def test_engine_error_counts_as_wrong_and_confusion_error():
    report=a8.run('mixed','rules');r=report['records'][0];r.update(status=None,error='Timeout')
    labels=[{'case_id':r['case_id'],'expected':'Partially Compliant','label_origin':'human-entered-not-blinded'}]
    row=score([report],labels)['per_control'][0]
    assert row['accuracy']==0 and row['errors']==1
    assert row['confusion']['Partially Compliant']['ERROR']==1


def test_soa_preserves_applicability_when_control_fails():
    report=a8.run('nonconforming','rules');soa=a8.soa(report)
    assert soa['approval']=='DRAFT_NOT_APPROVED'
    assert all(r['applicable'] and r['implementation_status']=='Non-Compliant' for r in soa['entries'])
    assert all(not r['applicability_approved'] for r in soa['entries'])


def test_model_never_receives_reference_and_invalid_citation_fails(monkeypatch):
    client=MagicMock();client.chat.return_value={'message':{'content':json.dumps(dict(status='Compliant',rationale='test',evidence_ids=['FAKE']))}}
    monkeypatch.setattr(a8.ollama,'Client',lambda **_:client)
    c=a8.catalog()[0];e=a8.collect('mixed',c)
    with pytest.raises(ValueError):a8.assess(c,e,'llm')
    messages=json.dumps(client.chat.call_args.kwargs['messages'])
    assert 'designer_labels' not in messages and 'expected' not in messages
    assert 'mixed' not in messages and 'conforming' not in messages


def test_model_outage_is_error_not_rule_fallback(monkeypatch):
    monkeypatch.setattr(a8.ollama,'Client',MagicMock(side_effect=TimeoutError()))
    report=a8.run('conforming','llm')
    assert all(r['status'] is None and r['execution_source']=='error' for r in report['records'])


@pytest.mark.parametrize('method,path', [('GET','catalog'),('GET','runs'),('POST','runs')])
def test_api_checks_membership(monkeypatch,method,path):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend import a8_api
    from backend.team_api import require_user
    app.dependency_overrides[require_user]=lambda:{'user_id':'u'}
    def deny(*args):raise HTTPException(403,'Not a member')
    monkeypatch.setattr(a8_api,'require_campaign',deny)
    try:
        with TestClient(app) as client:
            r=client.request(method,'/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/a8/'+path,**({'json':{}} if method=='POST' else {}))
            assert r.status_code==403
    finally:app.dependency_overrides.pop(require_user,None)


@pytest.fixture
def api_env(monkeypatch,tmp_path):
    from backend import a8_api
    from backend.main import app
    from backend.team_api import require_user
    monkeypatch.setattr(a8_api,'STORE',tmp_path)
    monkeypatch.setattr(a8_api,'require_campaign',lambda *_:None)
    monkeypatch.setattr(a8_api.pool,'submit',MagicMock())
    actor={'user_id':'starter','role':'admin'}
    app.dependency_overrides[require_user]=lambda:actor
    yield a8_api,actor
    app.dependency_overrides.pop(require_user,None)


def test_persistent_job_guard_and_separate_human_review(api_env):
    from fastapi.testclient import TestClient
    from backend.main import app
    api,actor=api_env
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976'
    path=f'/api/assessments/{aid}/a8'
    with TestClient(app) as client:
        created=client.post(path+'/runs',json={'mode':'rules','profile':'mixed'})
        assert created.status_code==202
        rid=created.json()['run_id']
        assert client.post(path+'/runs',json={}).status_code==409
        actor['user_id']='observer'
        hidden=client.get(path+'/runs').json()[0]
        assert 'report' not in hidden and hidden['profile']=='Ẩn hồ sơ'
        pending=client.get(path+'/runs/'+rid).json()
        assert pending['blind'] and pending['profile']=='Ẩn hồ sơ'
        actor['user_id']='starter'
        api.worker(aid,rid,'mixed','rules')
        result=client.get(path+'/runs/'+rid).json()
        assert result['state']=='finished'
        assert all(r['accuracy'] is None for r in result['human_comparison']['per_control'])
        review={'control_id':'A.8.1','expected':'Non-Compliant','rationale':'Independent reviewer disagrees on evidence scope','report_sha256':result['report']['sha256']}
        assert client.post(path+'/runs/'+rid+'/reviews',json=review).status_code==409
        actor['user_id']='reviewer'
        assert client.post(path+'/runs/'+rid+'/reviews',json=review).status_code==200
        result=client.get(path+'/runs/'+rid).json()
        assert result['blind'] and 'report' not in result and 'designer_comparison' not in result
        assert 'mixed' not in json.dumps(result) and 'Partially Compliant' not in json.dumps(result)
        assert all('facts' not in r['evidence'] for r in result['evidence_pack'])
        assert client.post(path+'/runs/'+rid+'/reviews',json=review).status_code==409
        for c in a8.catalog()[1:]:
            review['control_id']=c['control_id']
            assert client.post(path+'/runs/'+rid+'/reviews',json=review).status_code==200
        result=client.get(path+'/runs/'+rid).json()
        row=result['human_comparison']['per_control'][0]
        assert row['rated']==1 and row['accuracy']==0
        assert result['reviews'][0]['reviewer_id']=='reviewer'
        # Revealed results do not permit post-hoc label changes.
        assert client.post(path+'/runs/'+rid+'/reviews',json=review).status_code==409
        summary=client.get(path+'/summary').json()
        assert summary['cohorts'][0]['human_by_run_reviewer']
        actor['role']='member'
        assert client.post(path+'/rubric/approval',json={'note':'Rubric reviewed with project supervisor'}).status_code==403
        actor['role']='admin'
        assert client.post(path+'/rubric/approval',json={'note':'Rubric reviewed with project supervisor'}).status_code==200
        decisions=[dict(control_id=c['control_id'],applicable=True,reason='Relevant to scoped lab services',treatment='Maintain or remediate according to evidence') for c in a8.catalog()]
        approved=client.post(path+'/runs/'+rid+'/soa-approval',json={'note':'Scope reviewed and treatment plan recorded','decisions':decisions})
        assert approved.status_code==200
        approved_soa=client.get(path+'/runs/'+rid).json()['soa']
        assert approved_soa['approval']=='HUMAN_APPROVED_LIMITED_SCOPE'
        assert all(e['applicability_approved'] for e in approved_soa['entries'])
        other='00000000-0000-0000-0000-000000000001'
        assert client.get(f'/api/assessments/{other}/a8/runs/{rid}').status_code==404



def test_restart_marks_only_running_jobs_failed(api_env):
    api,_=api_env
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976'
    rid='00000000-0000-0000-0000-000000000001'
    api.save(api.folder(aid)/(rid+'.json'),{'state':'running','reviews':[]})
    api.recover_interrupted()
    assert api.read(aid,rid)['state']=='failed'


def test_assessor_cannot_create_answer_key_run_or_export_all_labels(api_env):
    from fastapi.testclient import TestClient
    from backend.main import app
    api,actor=api_env
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976'
    base=f'/api/assessments/{aid}/a8'
    with TestClient(app) as client:
        created=client.post(base+'/runs',json={'mode':'rules','profile':'mixed'}).json()
        rid=created['run_id']
        assert 'designer_reference' not in created
        assert api.read(aid,rid)['designer_reference']
        api.worker(aid,rid,'mixed','rules')
        actor.update(user_id='blind-assessor',role='assessor')
        assert client.get(base+'/catalog').json()['can_start'] is False
        assert client.post(base+'/runs',json={'mode':'rules'}).status_code==403
        hidden=client.get(base+'/runs/'+rid).json()
        for c in a8.catalog():
            response=client.post(base+'/runs/'+rid+'/reviews',json={'control_id':c['control_id'],
                'expected':'Partially Compliant','rationale':'Isolated test label, not a real human rating',
                'report_sha256':hidden['report_sha256']})
            assert response.status_code==200
        visible=client.get(base+'/runs/'+rid).json()
        assert 'report' in visible and 'designer_reference' not in visible
        assert all(row['case_id'].endswith('-mixed') for row in visible['designer_comparison']['cases'])


def test_run_records_provenance_and_soa_points_to_same_report():
    report=a8.run('mixed','rules')
    assert report['model'] is None
    assert report['catalog_sha256']==a8.digest(a8.catalog())
    assert all(r['criteria_checks'] for r in report['records'])
    soa=a8.soa(report)
    assert soa['report_sha256']==report['sha256']
    assert [r['evidence_sha256'] for r in soa['entries']]==[r['evidence']['source_sha256'] for r in report['records']]



def test_unavailable_docker_is_not_fake_success(api_env,monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    api,_=api_env
    monkeypatch.setattr(api,'runtime_status',lambda:'unavailable')
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976'
    with TestClient(app) as client:
        r=client.post(f'/api/assessments/{aid}/a8/runs',json={'transport':'docker'})
        assert r.status_code==503
        assert client.get(f'/api/assessments/{aid}/a8/runs').json()==[]
