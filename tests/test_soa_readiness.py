from datetime import date
import copy
import pytest
from backend.soa_readiness import build_readiness
from backend.review_criteria import validate_sources
from backend.scope56 import build_scope


def control():
    return dict(control_id='A.8.13',name='Backup',human_review_current=True,workflow_status='COMPLETED',
        applicability=dict(applicable=True,reason='Used by enterprise services',treatment='Maintain and retest backups',
            treatment_owner='Backup owner',treatment_due='2026-11-20',verification_plan='Restore sample and compare content hashes'))


def test_legacy_followup_cannot_be_approved_even_with_a_current_human_review():
    row=control();row['applicability'].pop('treatment_owner')
    result=build_readiness([row],True,date(2026,11,18))
    assert not result['approval_ready'] and result['pending_controls']==['A.8.13']
    assert result['controls'][0]['blockers']==['owner_missing']
    row['applicability'].pop('verification_plan');row['applicability'].pop('treatment_due')
    result=build_readiness([row],True,date(2026,11,18))
    assert set(result['controls'][0]['blockers'])=={'owner_missing','verification_missing','due_missing'}


def test_due_dates_are_advisory_not_a_fake_task_completion_or_daily_approval_change():
    row=control();original=copy.deepcopy(row)
    for as_of,state in [(date(2026,11,18),'scheduled'),(date(2026,11,20),'due_today'),(date(2026,11,21),'past_due_date')]:
        r=build_readiness([row],True,as_of)
        assert r['approval_ready'] and r['controls'][0]['due_state']==state
    assert row==original
    assert not build_readiness([row],False)['approval_ready']


def test_invalid_date_and_running_work_block_approval():
    row=control();row['applicability']['treatment_due']='2026-02-30';row['workflow_status']='RUNNING'
    r=build_readiness([row],True)
    assert not r['approval_ready'] and set(r['controls'][0]['blockers'])=={'running','due_invalid'}


def test_exclusion_requires_reason_but_does_not_invent_evidence_or_follow_up():
    row=control();row['applicability']={'applicable':False,'reason':'Excluded with recorded project justification'};row['human_review_current']=False
    r=build_readiness([row],True)
    assert r['approval_ready'] and r['controls'][0]['due_date'] is None
    row['applicability']['reason']='x'
    assert not build_readiness([row],True)['approval_ready']


def test_unusable_evidence_cannot_confirm_met_or_not_met_but_can_document_unknown():
    source=[{'evidence_id':'bad','source_quality':{'usable':False}}]
    for verdict in ['met','not_met']:
        with pytest.raises(ValueError):validate_sources([dict(verdict=verdict,evidence_ids=['bad'])],source)
    validate_sources([dict(verdict='unknown',evidence_ids=['bad'])],source)
    with pytest.raises(ValueError):validate_sources([dict(verdict='unknown',evidence_ids=['foreign'])],source)


def test_old_conclusive_review_is_preserved_but_not_current_when_source_is_unusable():
    evidence=dict(evidence_id='bad',sha256_hash='hash',source='provided',is_synthetic=False,source_quality={'usable':False})
    dossier={'controls':[dict(control_id='A.6.1',evidence=[evidence])]}
    first=build_scope('a',dossier);c=first['controls'][0]
    review=dict(review_token=c['review_token'],protocol='human-criteria-review-v2',conclusion='Compliant',
        evidence_ids=['bad'],criteria_reviews=[dict(criterion_index=i,verdict='met',evidence_ids=['bad'],rationale='Checked this source in the recorded review') for i,_ in enumerate(c['pass_criteria'])])
    result=build_scope('a',dossier,reviews={'A.6.1':review})
    assert result['controls'][0]['human_review']==review
    assert not result['controls'][0]['human_review_current']
    assert not result['soa']['approval_ready']
