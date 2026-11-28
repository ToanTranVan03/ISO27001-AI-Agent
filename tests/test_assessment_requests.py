from uuid import UUID
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from backend import enterprise_api as api


def test_request_schema_requires_scope_and_reason():
    with pytest.raises(ValidationError):api.AssessmentRequestInput(title='Test request',objective='Valid objective',control_ids=[],note='Valid request reason')


def test_operator_cannot_create_or_cancel(monkeypatch):
    from backend import remediation_api
    monkeypatch.setattr(remediation_api,'membership',lambda *_:'operator')
    req=api.AssessmentRequestInput(title='Test request',objective='Collect original records',control_ids=['A.6.1'],note='Synthetic test request only')
    with pytest.raises(HTTPException) as exc:api.create_assessment_request(UUID(int=1),req,{'user_id':'operator'})
    assert exc.value.status_code==403
    with pytest.raises(HTTPException):api.cancel_assessment_request(UUID(int=1),UUID(int=2),api.CancelAssessmentRequest(expected_version=1,note='Synthetic cancellation reason'),{'user_id':'operator'})


def test_duplicate_or_unknown_control_is_rejected(monkeypatch):
    from backend import remediation_api
    monkeypatch.setattr(remediation_api,'membership',lambda *_:'consultant')
    monkeypatch.setattr(api,'scope56',lambda *_:{'controls':[{'control_id':'A.6.1'}]})
    for ids in [['A.6.1','A.6.1'],['A.99.1']]:
        req=api.AssessmentRequestInput(title='Test request',objective='Collect original records',control_ids=ids,note='Synthetic request reason')
        with pytest.raises(HTTPException) as exc:api.create_assessment_request(UUID(int=1),req,{'user_id':'consultant'})
        assert exc.value.status_code==422
