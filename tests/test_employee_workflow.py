from copy import deepcopy
import pytest
from backend.employee_workflow import apply_event,document_hash,training_feedback


def case(kind='training'):
    return dict(kind=kind,user_id='employee',target_id='DEVICE-1',state='WAITING_EMPLOYEE',document_sha256=document_hash('policy v1'),responses=[],observations=[],reviews=[],history=[])


def event(doc,command,actor='employee',role='operator',**payload):
    return apply_event(doc,command,dict(note='Synthetic observation for software test only',**payload),actor,role,'2026-11-27T00:00:00Z')


def test_training_followup_is_not_a_pass_and_retest_preserves_answer():
    d=case();original=deepcopy(d)
    d=event(d,'respond',answer='Tôi chưa biết cách xử lý sự kiện này')
    assert d['responses'][0]['feedback']['followup'] and d['responses'][0]['feedback']['human_review_required']
    assert d['state']=='AWAITING_REVIEW' and original==case()
    with pytest.raises(PermissionError):event(d,'review',outcome='accepted',evidence=[{'evidence_id':'source'}])
    d=event(d,'review','reviewer','verifier',outcome='rework')
    d=event(d,'respond',answer='Nội dung giả mạo đáng ngờ; không bấm link và báo cáo SOC qua kênh nội bộ')
    assert len(d['responses'])==2 and d['state']=='AWAITING_REVIEW'
    assert all(d['responses'][-1]['feedback']['checks'].values())


def test_nda_requires_owner_acknowledgment_and_exact_document_hash():
    d=case('nda')
    with pytest.raises(PermissionError):event(d,'respond','consultant','consultant',answer='Pretend employee response',acknowledged=True,document_sha256=d['document_sha256'])
    with pytest.raises(ValueError):event(d,'respond',answer='Read the document',acknowledged=True,document_sha256='wrong')
    with pytest.raises(ValueError):event(d,'respond',answer='Read the document',acknowledged=False,document_sha256=d['document_sha256'])
    result=event(d,'respond',answer='Read this exact version',acknowledged=True,document_sha256=d['document_sha256'])
    assert result['state']=='AWAITING_REVIEW'


def test_mfa_keeps_enrollment_separate_from_enforcement_and_observer_cannot_verify():
    d=event(case('mfa'),'respond',answer='I will enroll using the approved channel')
    assert d['state']=='WAITING_SOURCE'
    with pytest.raises(PermissionError):event(d,'observe',role='business_admin',enrolled=True,enforced=True,evidence=[{'evidence_id':'source'}])
    d=event(d,'observe','observer','business_admin',enrolled=True,enforced=False,evidence=[{'evidence_id':'source'}])
    with pytest.raises(PermissionError):event(d,'review','observer','consultant',outcome='accepted',evidence=[{'evidence_id':'source'}])
    with pytest.raises(ValueError):event(d,'review','reviewer','verifier',outcome='accepted',evidence=[{'evidence_id':'source'}])
    d=event(d,'review','reviewer','verifier',outcome='rework')
    d=event(d,'observe','observer','business_admin',enrolled=True,enforced=True,evidence=[{'evidence_id':'new-source'}])
    d=event(d,'review','reviewer','verifier',outcome='accepted',evidence=[{'evidence_id':'new-source'}])
    assert d['state']=='REVIEWED' and len(d['observations'])==2
    with pytest.raises(PermissionError):event(d,'reopen','observer','consultant')
    d=event(d,'reopen','reviewer','verifier')
    assert d['state']=='REWORK' and len(d['reviews'])==2


def test_asset_return_needs_matching_receipt_source_and_separate_reviewer():
    d=event(case('asset_return'),'respond',answer='Device prepared for handover; physical receipt pending')
    with pytest.raises(ValueError):event(d,'observe','observer','business_admin',asset_id='WRONG',receipt_reference='R-1',evidence=[{'evidence_id':'source'}])
    with pytest.raises(ValueError):event(d,'observe','observer','business_admin',asset_id='DEVICE-1',receipt_reference='R-1',evidence=[])
    d=event(d,'observe','observer','business_admin',asset_id='DEVICE-1',receipt_reference='R-1',evidence=[{'evidence_id':'source'}])
    with pytest.raises(ValueError):event(d,'review','reviewer','verifier',outcome='accepted',evidence=[])
    result=event(d,'review','reviewer','verifier',outcome='accepted',evidence=[{'evidence_id':'source'}])
    assert result['state']=='REVIEWED' and 'returned' not in result


def test_submitted_and_superseded_answers_cannot_be_replayed():
    d=event(case(),'respond',answer='Synthetic submitted answer')
    with pytest.raises(ValueError):event(d,'respond',answer='Replace the first answer')
    d['state']='SUPERSEDED'
    with pytest.raises(ValueError):event(d,'respond',answer='Use an outdated version')
