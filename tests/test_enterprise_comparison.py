from backend.enterprise_comparison import summarize_periods
from backend.enterprise_comparison import period_fingerprint
import pytest
from pydantic import ValidationError
from backend.team_api import CampaignInput


def test_missing_stale_and_excluded_are_not_silently_passed():
    controls=[dict(control_id='A.6.1'),dict(control_id='A.6.2',latest_evaluation_id=1,conclusion='Compliant'),
        dict(control_id='A.6.3',latest_evaluation_id=2,conclusion='Compliant',assessment_state='stale'),
        dict(control_id='A.6.4',applicability={'applicable':False})]
    result=summarize_periods('client',[dict(assessment_id='p',name='Period',created_at='2026-11',controls=controls)])['periods'][0]
    assert result['compliant_share_percent']==33.33 and result['coverage_percent']==33.33
    assert result['counts']['Not Evaluated']==1 and result['counts']['Needs Reassessment']==1


def test_changes_do_not_assert_improvement_and_empty_denominator_stays_unknown():
    a=dict(assessment_id='a',name='Old',created_at='2026-01',controls=[dict(control_id='A.8.13')])
    b=dict(assessment_id='b',name='New',created_at='2026-03',controls=[dict(control_id='A.8.13',latest_evaluation_id=1,conclusion='Non-Compliant')])
    result=summarize_periods('client',[a,b])
    assert len(result['periods'][1]['changes'])==1 and not result['certification_claim']
    assert summarize_periods('c',[dict(a,controls=[])])['periods'][0]['compliant_share_percent'] is None


def test_fingerprint_ignores_report_generation_time_but_tracks_sources_and_review():
    rows=[dict(control_id='A.8.13',review_token='before',conclusion='Insufficient Evidence')]
    first=period_fingerprint(rows)
    assert first==period_fingerprint([dict(rows[0],generated_at='later')])
    assert first!=period_fingerprint([dict(rows[0],review_token='after')])


def test_period_requires_a_valid_pair_of_calendar_dates():
    args=dict(name='Monthly scope',isms_scope='One service and authorized users')
    with pytest.raises(ValidationError):CampaignInput(**args,period_start='2024-01-01')
    with pytest.raises(ValidationError):CampaignInput(**args,period_start='2024-02-01',period_end='2024-01-01')
    assert CampaignInput(**args,period_start='2024-01-01',period_end='2024-01-31',assessment_kind='monthly').assessment_kind=='monthly'
