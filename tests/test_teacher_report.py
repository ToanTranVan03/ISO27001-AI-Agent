import copy
import json
from pathlib import Path
import pytest
from fastapi import HTTPException
from backend.teacher_report import build_report
from backend.scope56 import build_scope
from agent_core.a8_assessment import digest


def sample():return json.loads(Path('docs/a8-results/live-v2-ollama-pilot.json').read_text(encoding='utf-8'))


def test_teacher_report_keeps_simulated_and_formal_results_separate():
    scope=build_scope('a',{'controls':[]});run=sample();before=copy.deepcopy(run)
    result=build_report(scope,[run],dict(simulated_label_count=54,human_label_count=0))
    assert run==before and result['professional_acceptance']=='NOT_ASSERTED'
    assert len(result['controls'])==56 and len(result['experiments'])==1
    e=result['experiments'][0]
    assert e['control_count']==18 and e['capture_count']==18
    assert e['source_coverage']==18 and e['first_errors']==1 and e['final_errors']==0
    assert e['pending_human_comparison'] and not e['human_comparisons']
    assert result['formal_conclusions']=={'Chưa đánh giá':56}


def test_invalid_reports_are_disclosed_instead_of_changing_denominators_silently():
    bad=sample();bad['report']['records'][0]['status']='Compliant'
    empty=sample();empty['report']['records']=[]
    empty['report']['sha256']=digest({k:v for k,v in empty['report'].items() if k!='sha256'})
    result=build_report(build_scope('a',{'controls':[]}),[bad,empty],{})
    assert not result['experiments'] and len(result['rejected_runs'])==2


def test_teacher_report_is_admin_only(monkeypatch):
    from backend import enterprise_api
    monkeypatch.setattr(enterprise_api,'require_campaign',lambda *_:None)
    with pytest.raises(HTTPException) as error:enterprise_api.teacher_report('a',dict(role='assessor'))
    assert error.value.status_code==403


def test_old_reports_with_missing_metadata_remain_explicit_legacy_history():
    run=sample();run['report'].pop('transport');run['report'].pop('catalog_sha256')
    run['report']['sha256']=digest({k:v for k,v in run['report'].items() if k!='sha256'})
    result=build_report(build_scope('a',{'controls':[]}),[run],{})
    item=result['experiments'][0]
    assert item['transport']=='UNKNOWN_LEGACY' and item['catalog_sha256'] is None
    assert item['metadata_complete'] is False
