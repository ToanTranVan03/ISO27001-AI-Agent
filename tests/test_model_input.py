import copy
import json
import pytest
from agent_core.model_input import pack_evidence,validate_budget,InputBudgetExceeded


def capture(eid,observed='2026-11-18T00:00:00Z',run='one'):
    return dict(evidence_id=eid,source='a8-capture://'+run,sha256_hash=eid,content=json.dumps(dict(origin='a8-live-capture-v1',
        artifacts=[{'artifact':'probe.json','content':'original source','sha256':'hash'}],criteria_scope=['criterion'],
        observed_at=observed,asset_id='asset',is_synthetic=True,provenance_verified=False,note='Limited lab scope',
        collected_at=run,run_id=run,assessment_id='assessment',report_sha256=run)))


def test_lossless_grouping_keeps_every_source_id_artifact_and_provenance():
    data=[capture('e1'),capture('e2',run='two')];original=copy.deepcopy(data)
    out=pack_evidence(data)
    assert len(out)==1 and out[0]['equivalent_evidence_ids']==['e1','e2']
    for source,provenance in zip(data,out[0]['provenance']):
        restored={**out[0]['content'],**{k:v for k,v in provenance.items() if k not in ('evidence_id','source','sha256_hash')}}
        assert restored==json.loads(source['content'])
    assert data==original


def test_different_observations_or_assets_are_never_merged():
    assert len(pack_evidence([capture('one'),capture('two',observed='2026-11-19T00:00:00Z')]))==2
    other=capture('two');p=json.loads(other['content']);p['asset_id']='another';other['content']=json.dumps(p)
    assert len(pack_evidence([capture('one'),other]))==2
    raw={'evidence_id':'text','content':'Ordinary supplied document'}
    assert pack_evidence([raw])==[raw]


def test_prompt_budget_counts_utf8_bytes_and_never_silently_truncates():
    with pytest.raises(InputBudgetExceeded):validate_budget([{'content':'ồ'*5000}])
    assert validate_budget([{'content':'abc'}])==3


def test_oversize_source_does_not_call_model_or_create_a_guessed_conclusion(monkeypatch):
    from agent_core import graph_builder
    monkeypatch.setattr(graph_builder,'get_rubric',lambda cid:None)
    monkeypatch.setattr(graph_builder.ollama,'Client',lambda **kwargs:pytest.fail('Oversize source must not call model'))
    with pytest.raises(InputBudgetExceeded):
        graph_builder.node_evaluate(dict(control_id='A.6.1',control_name='Screening',audit_trail=[],
            source_mode='user_evidence_only',collected_evidences=[dict(evidence_id='large',content='Long original source '*10000)]))
