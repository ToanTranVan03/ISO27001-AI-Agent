import copy
import json
from pathlib import Path
import pytest
from fastapi import HTTPException
from agent_core.a8_simulated_review import simulate
from agent_core.a8_assessment import digest
from agent_core.a8_review_analysis import analyze_reviews,declared_independent


def report():
    return json.loads(Path('docs/a8-results/live-v2-ollama-pilot.json').read_text(encoding='utf-8'))['report']


def test_simulation_is_reproducible_evidence_bound_and_not_prediction_copy():
    source=report();before=copy.deepcopy(source)
    result=simulate(source)
    assert source==before and result==simulate(source)
    assert len(result['labels'])==18 and result['human_label_count']==0
    assert not result['eligible_for_soa_approval']
    source['records'][0]['status']='Non-Compliant'
    source['sha256']=digest({k:v for k,v in source.items() if k!='sha256'})
    changed=simulate(source)
    assert changed['labels'][0]['expected']==result['labels'][0]['expected']
    assert changed['simulated_comparison']['cases'][0]['correct'] is False


def test_simulated_labels_cannot_count_as_human_even_with_false_independence_flags():
    source=report();labels=simulate(source)['labels']
    for row in labels:row.update(assistance='unassisted',prior_exposure='no')
    assert not any(declared_independent(row) for row in labels)
    analysis=analyze_reviews(source,labels,'coordinator')
    assert analysis['rejected_labels']==18
    assert analysis['submitted_label_count']==0 and not analysis['complete_independent_reviewers']


def test_tampered_report_artifact_and_malformed_facts_are_rejected():
    source=report();source['records'][0]['status']='Compliant'
    with pytest.raises(ValueError,match='Report hash'):simulate(source)
    source=report();source['records'][0]['evidence']['artifacts'][0]['content']='changed'
    source['sha256']=digest({k:v for k,v in source.items() if k!='sha256'})
    with pytest.raises(ValueError,match='Artifact hash'):simulate(source)
    source=report();source['records'][0]['evidence']['facts']={}
    source['sha256']=digest({k:v for k,v in source.items() if k!='sha256'})
    with pytest.raises(ValueError,match='Criteria/facts'):simulate(source)


def test_simulation_endpoint_preserves_blinding_and_never_saves(monkeypatch):
    from backend import a8_api
    monkeypatch.setattr(a8_api,'require_campaign',lambda *_:None)
    monkeypatch.setattr(a8_api,'save',lambda *_:pytest.fail('Simulation must not write human reviews'))
    source=dict(state='finished',report=report(),reviews=[])
    monkeypatch.setattr(a8_api,'read',lambda *_:source)
    with pytest.raises(HTTPException) as error:a8_api.simulated_review('a','r',dict(role='assessor'))
    assert error.value.status_code==403
    assert len(a8_api.simulated_review('a','r',dict(role='admin'))['labels'])==18
    assert source['reviews']==[]


def test_assessor_practice_never_reads_or_writes_selected_run(monkeypatch):
    from backend import a8_api
    monkeypatch.setattr(a8_api,'require_campaign',lambda *_:None)
    monkeypatch.setattr(a8_api,'read',lambda *_:pytest.fail('Must not open a blind run'))
    monkeypatch.setattr(a8_api,'save',lambda *_:pytest.fail('Must not write reviewer labels'))
    result=a8_api.practice_simulated_review('a',dict(role='assessor'))
    assert result['practice_only'] and len(result['labels'])==18
    assert result['human_label_count']==0 and not result['eligible_for_soa_approval']
    assert not analyze_reviews(report(),result['labels'],'creator')['submitted_label_count']


def test_saved_practice_is_account_isolated_and_not_a_real_review(monkeypatch,tmp_path):
    from backend import a8_api
    monkeypatch.setattr(a8_api,'require_campaign',lambda *_:None)
    monkeypatch.setattr(a8_api,'folder',lambda *_:tmp_path)
    a=dict(user_id='00000000-0000-0000-0000-000000000001',display_name='Practice A')
    b=dict(user_id='00000000-0000-0000-0000-000000000002',display_name='Practice B')
    first=a8_api.save_practice_simulated_review('campaign',a)
    assert first==a8_api.practice_simulated_review('campaign',a)
    assert first['performed_by']=='SIMULATED_RUBRIC_ENGINE_NOT_ACCOUNT_HOLDER'
    assert 'practice_account_id' not in a8_api.practice_simulated_review('campaign',b)
    second=a8_api.save_practice_simulated_review('campaign',b)
    assert first['practice_account_id']!=second['practice_account_id']
    assert len(list(tmp_path.glob('*.json')))==0
    assert len(list((tmp_path/'practice').glob('*.json')))==2
    summary=a8_api.practice_summary('campaign',dict(role='admin'))
    assert len(summary['accounts'])==2 and summary['simulated_label_count']==36
    assert summary['human_label_count']==0
    with pytest.raises(HTTPException) as error:a8_api.practice_summary('campaign',dict(role='assessor'))
    assert error.value.status_code==403
