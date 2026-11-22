import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import app
from backend.team_api import require_user
from backend import enterprise_api
from evidence_collectors import source_intake,control_packages

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'


def test_preflight_checks_membership_and_never_stores(monkeypatch):
    client=TestClient(app)
    base=f'/api/assessments/{AID}/enterprise/scope56/controls/A.6.1/sources/validate'
    c=source_intake.controls()[0]
    form={'evidence_type':c['expected_evidence_types'][0],'origin':'Synthetic technical test'}
    def post(raw):return client.post(base,data=form,files={'file':('record.txt',raw)})
    assert post(b'x').status_code==401
    app.dependency_overrides[require_user]=lambda:{'user_id':'test','role':'member'}
    def forbidden(*args,**kwargs):raise AssertionError('Validation must not persist')
    monkeypatch.setattr(source_intake,'preserve',forbidden)
    monkeypatch.setattr(control_packages,'store',forbidden)
    try:
        def deny(*args):raise HTTPException(403,'Not a member')
        monkeypatch.setattr(enterprise_api,'require_campaign',deny)
        assert post(b'x').status_code==403
        monkeypatch.setattr(enterprise_api,'require_campaign',lambda *_:None)
        assert post(b'x').status_code==422
        good=post(b'Synthetic source data for API verification, not an actual audit record.')
        assert good.status_code==200
        value=good.json()
        assert value['preflight_only'] and not value['evidence_saved'] and not value['original_preserved']
        assert value['quality']['usable'] and value['warnings']
        assert 'Synthetic source data' not in good.text
    finally:app.dependency_overrides.pop(require_user,None)
