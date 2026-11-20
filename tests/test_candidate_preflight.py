import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.team_api import require_user
from backend import a8_api,validation_plan


def test_preflight_checks_permissions_and_never_starts_worker(monkeypatch):
    client=TestClient(app);url='/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/a8/candidate-runs/validate'
    assert client.post(url,json={'plan':{}}).status_code==401
    user={'user_id':'test','role':'assessor'}
    app.dependency_overrides[require_user]=lambda:user
    monkeypatch.setattr(a8_api,'require_campaign',lambda *args:None)
    monkeypatch.setattr(a8_api.pool,'submit',lambda *args:pytest.fail('Preflight must not start worker'))
    monkeypatch.setattr(a8_api,'save',lambda *args:pytest.fail('Preflight must not save a run'))
    try:
        assert client.post(url,json={'plan':{}}).status_code==403
        user['role']='admin'
        monkeypatch.setattr(validation_plan,'validate_candidate',lambda plan:{'sha256':'sealed','snapshot':{'evidence':[{'control_id':'A.8.1','artifacts':[],'facts':{'check':None}}]}})
        r=client.post(url,json={'plan':{}})
        assert r.status_code==200 and r.json()['model_called'] is False and r.json()['run_created'] is False
        assert r.json()['controls'][0]['unknown_checks']==['check']
        def invalid(plan):raise ValueError('Source hash mismatch')
        monkeypatch.setattr(validation_plan,'validate_candidate',invalid)
        assert client.post(url,json={'plan':{}}).status_code==422
    finally:app.dependency_overrides.pop(require_user,None)
