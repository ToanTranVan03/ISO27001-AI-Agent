from copy import deepcopy
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend import enterprise_api as api,a8_api
from backend.team_api import require_user
from backend.decision_batch import preview

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'


def decision(cid='A.6.1'):
    return dict(control_id=cid,applicable=True,reason='Synthetic test scope rationale',
        treatment='Synthetic test collection plan',treatment_owner=None,treatment_due=None,verification_plan=None)


@pytest.fixture
def scenario(monkeypatch,tmp_path):
    actor={'user_id':'test-owner','role':'admin'}
    state={'assessment_id':AID,'rubric_approval':None,'soa':{'fingerprint':'a'*64},
        'controls':[dict(control_id=cid,name=cid,applicability=None,human_review_current=False,workflow_status='NOT_STARTED') for cid in ('A.6.1','A.6.2')]}
    app.dependency_overrides[require_user]=lambda:actor
    monkeypatch.setattr(api,'require_campaign',lambda *args:None)
    monkeypatch.setattr(api,'scope56',lambda *args:deepcopy(state))
    monkeypatch.setattr(a8_api,'STORE',tmp_path)
    yield actor,state,a8_api.folder(AID)/'settings'/'scope56-decisions.json'
    app.dependency_overrides.pop(require_user,None)


def payload():
    return dict(assessment_id=AID,expected_fingerprint='a'*64,decisions=[decision()],note='Synthetic batch import test only; no real owner decision')


def test_preview_is_read_only_and_exposes_missing_follow_up(scenario):
    actor,state,path=scenario;before=deepcopy(state)
    with TestClient(app) as client:
        r=client.post(f'/api/assessments/{AID}/enterprise/scope56/decisions/batch/validate',json=payload())
    assert r.status_code==200 and r.json()['changed_count']==1
    assert r.json()['projected_ready_controls']==0 and r.json()['changes'][0]['remaining_blockers']
    assert not path.exists() and state==before


def test_all_changes_commit_once_with_identity_and_unchanged_import_is_noop(scenario):
    actor,state,path=scenario;p=payload();p['decisions'].append(decision('A.6.2'))
    with TestClient(app) as client:
        r=client.post(f'/api/assessments/{AID}/enterprise/scope56/decisions/batch',json=p)
        assert r.status_code==200 and r.json()['applied']==2
        history=json.loads(path.read_text(encoding='utf-8'));assert len(history)==2
        assert all(d['recorded_by']=='test-owner' and d['import_batch_id']==r.json()['import_batch_id'] for d in history)
        for c,d in zip(state['controls'],history):c['applicability']=d
        saved=path.read_bytes()
        repeat=client.post(f'/api/assessments/{AID}/enterprise/scope56/decisions/batch',json=p)
        assert repeat.status_code==200 and repeat.json()['applied']==0
        assert path.read_bytes()==saved


@pytest.mark.parametrize('kind,code',[('stale',409),('campaign',409),('duplicate',422),('outside',422),('assessor',403),('invalid_date',422),('string_boolean',422)])
def test_invalid_or_unauthorized_batch_never_partially_writes(scenario,kind,code):
    actor,state,path=scenario;p=payload()
    if kind=='stale':state['soa']['fingerprint']='b'*64
    elif kind=='campaign':p['assessment_id']='00000000-0000-0000-0000-000000000001'
    elif kind=='duplicate':p['decisions']*=2
    elif kind=='outside':p['decisions'].append(decision('A.8.35'))
    elif kind=='assessor':actor['role']='assessor'
    elif kind=='invalid_date':p['decisions'][0]['treatment_due']='2026-02-30'
    else:p['decisions'][0]['applicable']='false'
    with TestClient(app) as client:
        for suffix in ('/validate',''):
            r=client.post(f'/api/assessments/{AID}/enterprise/scope56/decisions/batch'+suffix,json=p)
            assert r.status_code==code,(kind,r.text)
    assert not path.exists()


def test_storage_failure_is_visible_and_retains_prior_history(scenario,monkeypatch):
    actor,state,path=scenario;path.parent.mkdir(parents=True);path.write_text('[{"history":"preserved"}]',encoding='utf-8')
    before=path.read_bytes()
    def fail(*args):raise PermissionError('Synthetic storage failure')
    monkeypatch.setattr(a8_api,'save',fail)
    with TestClient(app) as client:
        r=client.post(f'/api/assessments/{AID}/enterprise/scope56/decisions/batch',json=payload())
    assert r.status_code==503 and path.read_bytes()==before
