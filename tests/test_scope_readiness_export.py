import copy
import json
import pytest
from backend.scope56 import build_scope
from scripts.export_scope_readiness import export,source_states


def test_export_is_read_only_complete_and_cannot_overwrite_history(tmp_path):
    scope=build_scope('campaign',{'controls':[]});before=copy.deepcopy(scope)
    destination=tmp_path/'run'
    result=export(scope,destination)
    assert result['read_only'] and not result['human_assessment']
    packet=json.loads((destination/'handoff.json').read_text(encoding='utf-8'))
    assert len(packet['controls'])==56 and scope==before
    assert 'MISSING_EVIDENCE' in (destination/'controls.csv').read_text(encoding='utf-8-sig')
    with pytest.raises(FileExistsError):export(scope,destination)


def test_source_states_keep_integrity_coverage_and_content_separate():
    row={'gaps':['source_content_unusable','source_integrity_failed','human_criteria_review_not_current'],
         'sources':[{'source_quality':{'integrity':{'state':'failed'}}}]}
    states=source_states(row)
    assert 'EVIDENCE_RECORDED' in states and 'MISSING_EVIDENCE' not in states
    assert {'INTEGRITY_FAILED','UNUSABLE_CONTENT','COVERAGE_NOT_CONFIRMED'} <= set(states)
    row['gaps']=[];row['sources']=[{}]
    assert source_states(row)==['EVIDENCE_RECORDED','ORIGINAL_NOT_FULLY_VERIFIED']
