from copy import deepcopy
import pytest
from pydantic import ValidationError
from backend.remediation import dashboard
from backend.remediation_api import Advice


def test_empty_dashboard_does_not_invent_progress_or_compliance():
    result=dashboard([],[], '2026-11-22')
    assert result['completion_percent'] is None and result['actions']==0
    assert result['estimated_cost'] is None and result['conclusions']=={}


def test_dashboard_distinguishes_deadlines_source_quality_and_human_steps():
    records=[dict(kind='finding',record_id='f',document=dict(control_id='A.8.13',description='Test backup gap',risk='high',actions=[
        dict(state='IN_PROGRESS',due_date='2026-11-21'),dict(state='AWAITING_VERIFICATION',due_date='2026-11-25'),dict(state='CLOSED',due_date='2020-01-01')]))]
    controls=[dict(control_id='A.8.13',conclusion='Insufficient Evidence',evidence=[dict(is_synthetic=False,source_quality={'usable':False})])]
    original=deepcopy(records)
    result=dashboard(records,controls,'2026-11-22')
    assert result['overdue']==1 and result['due_soon']==1 and result['completion_percent']==33.33
    assert {'unusable_sources','needs_review','needs_applicability','remediating','awaiting_verification','has_verified_action'}<=set(result['worklist'][0]['flags'])
    assert 'Thay thế nguồn không đủ chất lượng' in result['worklist'][0]['required_tasks']
    assert len(result['remaining_issues'])==1 and result['urgent'][0]['control_id']=='A.8.13' and records==original


def test_ai_requires_specific_advice_instead_of_only_generic_task_list():
    with pytest.raises(ValidationError):Advice(title='Generic',steps='Generic steps only',acceptance='Generic criterion',department='IT',resources='Owner',tasks=['Do something'])
