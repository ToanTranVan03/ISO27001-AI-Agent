import json
from uuid import uuid4
import pytest
from backend.enterprise_spec import NODE_SPECS, CONTROL_TO_NODE, PRESETS, make_snapshot


def test_enterprise_has_five_nodes_and_no_duplicate_control():
    assert len(NODE_SPECS) == 5
    assert len(CONTROL_TO_NODE) == 5
    assert {'A.6.1','A.7.1','A.8.5','A.8.13','A.8.20'} == set(CONTROL_TO_NODE)


def test_evidence_is_deterministic_and_explicitly_synthetic():
    campaign=str(uuid4())
    first=make_snapshot(campaign,'iam','partial',2)
    second=make_snapshot(campaign,'iam','partial',2)
    assert first==second
    assert first['source']=='lab://iam/v2'
    assert len(first['sha256_hash'])==64
    body=json.loads(first['extracted_text'])
    assert body['is_synthetic'] is True
    assert body['source_kind']=='SIMULATED_ENTERPRISE_LAB'
    assert 'expected_status' not in first['extracted_text']
    changed=make_snapshot(campaign,'iam','gap',3)
    assert changed['evidence_id'] != first['evidence_id']


@pytest.mark.parametrize('node',list(NODE_SPECS))
@pytest.mark.parametrize('mode',PRESETS)
def test_all_presets_have_usable_facts(node, mode):
    data=make_snapshot(str(uuid4()),node,mode,1)
    payload=json.loads(data['extracted_text'])
    assert payload['control_id'] in CONTROL_TO_NODE
    assert payload['facts']
    assert payload['scenario']==mode


def test_reject_invalid_node_or_scenario():
    campaign=str(uuid4())
    for args in [('iam','fake',1),('fake','healthy',1),('iam','healthy',0)]:
        with pytest.raises(ValueError):make_snapshot(campaign,*args)
