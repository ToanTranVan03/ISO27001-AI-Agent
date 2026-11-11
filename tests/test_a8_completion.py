"""Week 5 reliability and study workflow checks, without fake human study data."""
import copy
import json
from unittest.mock import MagicMock
import pytest
from agent_core import a8_assessment as a8
from agent_core.a8_benchmark import score
from agent_core.a8_protocol import prepare,execute
from agent_core.a8_review_analysis import analyze_reviews
from test_a8_assessment import api_env


def response(status,eid):
    return {'message':{'content':json.dumps(dict(status=status,rationale='Model evaluation based on captured evidence',evidence_ids=[eid]))}}


def test_repair_keeps_first_error_and_scores_first_pass_separately(monkeypatch):
    c=a8.catalog()[0];e=a8.collect('mixed',c)
    client=MagicMock()
    client.chat.side_effect=[response('Non-Compliant',e['evidence_id']),response('Partially Compliant',e['evidence_id'])]
    monkeypatch.setattr(a8.ollama,'Client',lambda **_:client)
    r=a8.assess_with_repair(c,e,'llm')
    assert r['repaired'] and r['status']=='Partially Compliant'
    assert r['attempts'][0]['error']=='RubricConclusionMismatch'
    assert r['attempts'][0]['diagnostic']['proposed_status']=='Non-Compliant'
    repair_message=client.chat.call_args.kwargs['messages'][-1]['content']
    assert 'Partially Compliant' not in repair_message
    report=a8.run('mixed','rules');record=report['records'][0];record.update(r)
    table=score([report],[dict(case_id=record['case_id'],expected='Partially Compliant')])['per_control'][0]
    assert table['accuracy']==1 and table['first_pass_accuracy']==0 and table['repaired']==1


def test_repair_is_bounded_and_transport_outages_are_not_retried(monkeypatch):
    c=a8.catalog()[0];e=a8.collect('mixed',c)
    client=MagicMock();client.chat.return_value=response('Non-Compliant',e['evidence_id'])
    monkeypatch.setattr(a8.ollama,'Client',lambda **_:client)
    with pytest.raises(a8.RubricConclusionMismatch) as error:a8.assess_with_repair(c,e,'llm')
    assert client.chat.call_count==2 and len(error.value.attempts)==2
    client.reset_mock();client.chat.side_effect=TimeoutError()
    with pytest.raises(TimeoutError):a8.assess_with_repair(c,e,'llm')
    assert client.chat.call_count==1


def test_protocol_seals_sources_before_execution_and_never_recollects(monkeypatch):
    plan=prepare('mixed','files','test coordinator','Reproducible known-case check')
    assert not plan['independent_validation'] and plan['human_approval']=='PENDING'
    assert 'designer_labels' not in json.dumps(plan)
    monkeypatch.setattr(a8,'collect',lambda *_:pytest.fail('Frozen experiment must not collect new evidence'))
    result=execute(plan,'rules')
    assert result['report']['capture_sha256']==plan['snapshot']['sha256']
    assert result['report']['records'][0]['evidence']==plan['snapshot']['evidence'][0]
    changed=copy.deepcopy(plan);changed['snapshot']['evidence'][0]['facts']={}
    with pytest.raises(ValueError,match='modified'):execute(changed,'rules')
    changed=copy.deepcopy(plan);changed['recipe']['model']='another-model';changed['sha256']=a8.digest({k:v for k,v in changed.items() if k!='sha256'})
    with pytest.raises(ValueError,match='changed'):execute(changed,'rules')


def test_external_candidate_does_not_become_heldout_by_copying_capture_dates(tmp_path):
    import shutil
    from evidence_collectors import a8_raw
    original=a8_raw.ROOT
    shutil.copytree(original/'conforming',tmp_path/'conforming')
    for path in (tmp_path/'conforming').glob('*/capture.json'):
        data=json.loads(path.read_text(encoding='utf-8'));data['asset_id']='renamed-asset'
        path.write_text(json.dumps(data),encoding='utf-8')
    plan=prepare('conforming','files','coordinator','Unverified candidate',raw_root=tmp_path)
    assert a8_raw.ROOT==original
    assert len(plan['known_fixture_overlap_controls'])==18
    assert not plan['independent_validation']
    assert all(e['source_kind']=='external-lab-candidate-unverified' for e in plan['snapshot']['evidence'])
    with pytest.raises(ValueError,match='all 18'):prepare('mixed','files','coordinator','Empty candidate',raw_root=tmp_path)


def label(report,index,uid,status):
    r=report['records'][index]
    return dict(case_id=r['case_id'],control_id=r['control_id'],reviewer_id=uid,expected=status,assistance='unassisted',prior_exposure='no',
                rationale='Test only, not an independent expert judgment',report_sha256=report['sha256'],
                evidence_sha256=r['evidence']['source_sha256'])


def test_review_agreement_is_evidence_bound_and_does_not_invent_consensus():
    report=a8.run('mixed','rules')
    labels=[label(report,0,'a','Compliant'),label(report,1,'a','Non-Compliant'),
            label(report,0,'b','Compliant'),label(report,1,'b','Partially Compliant')]
    stale=label(report,2,'b','Compliant');stale['evidence_sha256']='wrong';labels.append(stale)
    labels.append(label(report,2,'creator','Compliant'))
    result=analyze_reviews(report,labels,'creator')
    assert result['rejected_labels']==2 and not result['complete_reviewers']
    pair=result['pairwise_agreement'][0]
    assert pair['paired_controls']==2 and pair['agreement']==0.5
    assert pair['cohens_kappa']==pytest.approx(1/3)
    assert len(result['disagreements'])==2
    assert all(d['resolution']=='PENDING_HUMAN_DISCUSSION' for d in result['disagreements'])
    with pytest.raises(ValueError,match='Duplicate'):analyze_reviews(report,labels+[labels[0]],'creator')


def test_api_does_not_mix_partial_reviewers_or_leak_protocol(api_env):
    from fastapi.testclient import TestClient
    from backend.main import app
    api,actor=api_env
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976';base=f'/api/assessments/{aid}/a8'
    with TestClient(app) as client:
        rid=client.post(base+'/runs',json={'profile':'mixed','mode':'rules'}).json()['run_id']
        api.worker(aid,rid,'mixed','rules')
        doc=api.read(aid,rid)
        assert doc['protocol']['snapshot']['sha256']==doc['report']['capture_sha256']
        doc['reviews']=[label(doc['report'],0,'reviewer-a','Compliant'),label(doc['report'],1,'reviewer-b','Non-Compliant')]
        api.save(api.folder(aid)/(rid+'.json'),doc)
        visible=client.get(base+'/runs/'+rid).json()
        assert visible['human_reference_reviewer_id'] is None
        assert all(r['rated']==0 for r in visible['human_comparison']['per_control'])
        assert len(visible['reviewer_comparisons'])==2
        progress=visible['review_analysis']['reviewer_progress']
        assert len(progress)==2 and all(r['submitted']==1 and r['total']==18 and not r['complete'] for r in progress)
        assert visible['review_analysis']['submitted_label_count']==2
        actor['user_id']='reviewer-a'
        hidden=client.get(base+'/runs/'+rid).json()
        assert hidden['blind'] and 'protocol' not in hidden and 'review_analysis' not in hidden
        actor['user_id']='starter'
        doc['reviews']=[label(doc['report'],i,'reviewer-a','Partially Compliant') for i in range(18)]
        api.save(api.folder(aid)/(rid+'.json'),doc)
        visible=client.get(base+'/runs/'+rid).json()
        assert visible['human_reference_reviewer_id']=='reviewer-a'
        assert all(r['accuracy']==1 for r in visible['human_comparison']['per_control'])


@pytest.mark.parametrize('facts',[{}, {'check':'false'}, {'check':0}, {'check':[] }])
def test_invalid_facts_cannot_pass_vacuously_or_by_truthiness(facts):
    with pytest.raises(ValueError):a8.rules({'facts':facts})


def test_missing_check_and_missing_reviewer_identity_are_rejected(monkeypatch):
    control=a8.catalog()[0];evidence=a8.collect('mixed',control)
    evidence['facts'].pop(next(iter(evidence['facts'])))
    monkeypatch.setattr(a8.ollama,'Client',lambda **_:pytest.fail('Malformed input must not call model'))
    with pytest.raises(ValueError):a8.assess(control,evidence,'llm')
    report=a8.run('mixed','rules')
    result=analyze_reviews(report,[label(report,0,None,'Compliant')],'creator')
    assert result['rejected_labels']==1 and not result['reviewer_comparisons']
