from uuid import uuid4
from contextlib import contextmanager
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backend import main, enterprise_missions as missions, incident_api
from backend.team_api import require_user


def test_scope_uses_control_domain_instead_of_workstation_type():
    scan={"findings":[{"control_id":"A.8.19","asset_id":"OFFICE-EMP-025"}, {"control_id":"A.7.10"}],"checked_assets":14}
    assert missions.scoped_scan(scan,"software")["findings"]==[scan["findings"][0]]
    assert len(scan["findings"])==2


def test_no_findings_is_not_a_compliance_certificate():
    report=missions.build_report({"findings":[]},[],{"findings":[]},[])
    assert report["blockers"]==[] and report["processed_count"]==0
    assert "56" in report["limitation"]
    assert "compliant" not in report


def test_unverified_response_and_remaining_events_block_approval():
    report=missions.build_report({"findings":[{}]},[{"incident_id":"case","verified":False}],{"findings":[{}]},[{"incident_id":"other"}])
    assert len(report["blockers"])==3
    assert report["incident_ids"]==["case"]


def test_department_plan_waits_for_real_results():
    doc=missions.new_document(uuid4(),"Review enterprise","all","user")
    assert doc["status"]=="queued"
    assert all(task["status"]=="waiting" and "output" not in task for task in doc["tasks"])
    assert doc["review"] is None and doc["is_synthetic"]


def test_failure_stops_downstream_handoffs(monkeypatch):
    doc=missions.new_document(uuid4(),"Review enterprise","all","tester")
    class Cursor:
        def execute(self,sql,args):
            self.result=(True,) if "pg_try" in sql else (deepcopy(doc),)
        def fetchone(self): return self.result
    class Connection:
        @contextmanager
        def cursor(self): yield Cursor()
    @contextmanager
    def connection(): yield Connection()
    saved=[]
    monkeypatch.setattr(missions,"get_connection",connection)
    monkeypatch.setattr(missions,"save",lambda aid,value:saved.append(deepcopy(value)))
    def fail(*args): raise RuntimeError("inventory unavailable")
    monkeypatch.setattr(missions,"inventory_snapshot",fail)
    missions.run_mission("assessment",doc["mission_id"])
    final=saved[-1]
    assert final["status"]=="failed"
    assert [task["status"] for task in final["tasks"]]==["completed","failed","blocked","blocked"]
    assert len(final["handoffs"])==1
    assert final["review"] is None


def test_mission_endpoints_require_login():
    with TestClient(main.app) as client:
        base=f'/api/assessments/{uuid4()}/enterprise/missions'
        assert client.get(base).status_code==401
        assert client.post(base,json={"request_id":str(uuid4()),"goal":"Review enterprise","scope":"all"}).status_code==401


def test_scope_validation_and_campaign_access(monkeypatch):
    checked=[]
    monkeypatch.setattr(incident_api,"require_campaign",lambda aid,user:checked.append(str(aid)))
    monkeypatch.setattr(missions,"list_missions",lambda aid:[])
    main.app.dependency_overrides[require_user]=lambda:{"user_id":"tester"}
    try:
        with TestClient(main.app) as client:
            aid=str(uuid4());base=f'/api/assessments/{aid}/enterprise/missions'
            assert client.get(base).json()==[] and checked==[aid]
            assert client.post(base,json={"request_id":str(uuid4()),"goal":"Review enterprise","scope":"unknown"}).status_code==422
            assert client.post(base+f'/{uuid4()}/review',json={"decision":"approve","note":"   "}).status_code==422
    finally:
        main.app.dependency_overrides.pop(require_user,None)
