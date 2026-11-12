from datetime import date
import pytest
from pydantic import ValidationError
from backend.enterprise_api import ScopeDecision
from backend.scope56 import build_scope


def decision(**kwargs):
    return ScopeDecision(control_id='A.8.13',applicable=True,
                         reason='Used by the lab enterprise',treatment='Repair and repeat restore test',**kwargs)


def test_follow_up_validates_dates_and_text_and_serializes_to_json():
    item=decision(treatment_owner='IT operations',treatment_due='2026-11-15',
                  verification_plan='Repeat restore and compare content hashes')
    assert item.treatment_due==date(2026,11,15)
    assert item.model_dump(mode='json')['treatment_due']=='2026-11-15'
    for args in [dict(treatment_due='2026-02-30'),dict(treatment_owner=' '),dict(verification_plan='done')]:
        with pytest.raises(ValidationError):decision(**args)
    assert decision().model_dump()['treatment_owner'] is None


def test_follow_up_is_exported_without_being_auto_approved_and_changes_fingerprint():
    initial=build_scope('a',{'controls':[]})
    decisions={c['control_id']:dict(applicable=False,reason='Recorded project scope decision',treatment='Retain exclusion rationale') for c in initial['controls']}
    old=build_scope('a',{'controls':[]},decisions=decisions)
    rubric=[dict(rubric_sha256=old['rubric_sha256'],approved_by='test-only')]
    approved=build_scope('a',{'controls':[]},decisions=decisions,rubric_approvals=rubric,
                         approvals=[dict(fingerprint=old['soa']['fingerprint'],approved_by='test-only')])
    assert approved['soa']['approval']=='HUMAN_APPROVED_PROJECT_SCOPE'
    decisions['A.8.13'].update(treatment_owner='Backup operator',treatment_due='2026-11-15',
                             verification_plan='Repeat restore test after correcting configuration')
    updated=build_scope('a',{'controls':[]},decisions=decisions,rubric_approvals=rubric,
                        approvals=[dict(fingerprint=old['soa']['fingerprint'],approved_by='test-only')])
    assert updated['soa']['approval']=='DRAFT_NOT_APPROVED'
    row=next(c for c in updated['soa']['entries'] if c['control_id']=='A.8.13')
    assert row['treatment_owner']=='Backup operator' and row['treatment_due']=='2026-11-15'
    packet=next(c for c in updated['handoff_packet']['controls'] if c['control_id']=='A.8.13')
    assert packet['recorded_follow_up']['owner']=='Backup operator'
    assert not packet['treatment_proposal']['approved']


def test_applicable_legacy_plan_requests_missing_followup_details():
    item=decision().model_dump(mode='json')
    scope=build_scope('a',{'controls':[]},decisions={'A.8.13':item})
    assert any(t['stage']=='treatment' and t['control_id']=='A.8.13' for t in scope['acceptance_worklist']['tasks'])
    item.update(treatment_owner='IT operator',treatment_due='2026-11-15',verification_plan='Compare restored file hashes')
    scope=build_scope('a',{'controls':[]},decisions={'A.8.13':item})
    assert not any(t['stage']=='treatment' and t['control_id']=='A.8.13' for t in scope['acceptance_worklist']['tasks'])
    assert scope['soa']['approval']=='DRAFT_NOT_APPROVED'
