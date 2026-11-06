from copy import deepcopy
from contextlib import contextmanager
from uuid import uuid4
import json
import pytest

from backend import enterprise_missions as missions, mission_planner as planner, incident_api, employee_commands


def valid_plan():
    return {"objective":"Kiểm tra máy và lập hồ sơ có bằng chứng",
            "steps":[{"tool":tool,"purpose":"Đọc và kiểm tra dữ liệu"} for tool in ["inventory","workstations","security","report"]],
            "checklist":["Đúng người và máy"]}


@pytest.mark.parametrize("names",[
    ["security","inventory","report"], ["inventory","report","security"],
    ["inventory","security","security","report"], ["inventory","workstations","report"],
    ["inventory","security","approve"], ["Bash","security","report"],
    ["inventory","security","report","workstations"],
])
def test_planner_rejects_unsafe_missing_or_repeated_steps(names):
    data=valid_plan();data["steps"]=[{"tool":name,"purpose":"Test operation"} for name in names]
    with pytest.raises(ValueError): planner.validate_plan(data)


def test_model_cannot_supply_shell_or_scope_arguments():
    data=valid_plan();data["steps"][0]["command"]="powershell something"
    with pytest.raises(ValueError): planner.validate_plan(data)
    data=valid_plan();data["scope"]="other-assessment"
    with pytest.raises(ValueError): planner.validate_plan(data)


def test_plan_requires_real_report_and_bounded_checklist():
    assert planner.validate_plan(valid_plan())["steps"][-1]["tool"]=="report"
    data=valid_plan();data["checklist"]=[" "]
    with pytest.raises(ValueError): planner.validate_plan(data)


def test_ollama_plan_has_timeout_and_explicit_provenance(monkeypatch):
    captured={}
    class Client:
        def __init__(self,**kwargs):captured.update(kwargs)
        def chat(self,**kwargs):
            captured["messages"]=kwargs["messages"]
            return {"message":{"content":json.dumps(valid_plan())}}
    monkeypatch.setattr(planner.ollama,"Client",Client)
    result=planner.plan_with_model("Kiểm tra máy nhân viên","hardware",[{"mission_id":"prior"}])
    assert result["source"]=="ollama_plan_and_execute" and result["scope"]=="hardware"
    assert captured["timeout"]==45
    assert "prior" in captured["messages"][-1]["content"]


def test_unavailable_and_invalid_model_outputs_are_not_success(monkeypatch):
    class Offline:
        def __init__(self,**kwargs):pass
        def chat(self,**kwargs):raise ConnectionError()
    monkeypatch.setattr(planner.ollama,"Client",Offline)
    with pytest.raises(planner.PlannerBlocked) as error: planner.plan_with_model("goal","all",[])
    assert error.value.code=="planner_unavailable"
    class Invalid(Offline):
        def chat(self,**kwargs):return {"message":{"content":'{"steps":[]}'}}
    monkeypatch.setattr(planner.ollama,"Client",Invalid)
    with pytest.raises(planner.PlannerBlocked) as error: planner.plan_with_model("goal","all",[])
    assert error.value.code=="invalid_plan"


@pytest.fixture
def worker(monkeypatch):
    state={"doc":None,"saved":[]}
    class Cursor:
        def execute(self,sql,args):self.result=(True,) if "pg_try" in sql else (deepcopy(state["doc"]),)
        def fetchone(self):return self.result
        def fetchall(self):return []
    class Connection:
        @contextmanager
        def cursor(self):yield Cursor()
    @contextmanager
    def connection():yield Connection()
    monkeypatch.setattr(missions,"get_connection",connection)
    monkeypatch.setattr(missions,"save",lambda aid,doc:state["saved"].append(deepcopy(doc)))
    monkeypatch.setattr(missions,"reviewed_memory",lambda aid,scope:[{"mission_id":"reviewed-case","review_note":"Kiểm tra máy"}])
    monkeypatch.setattr(missions,"inventory_snapshot",lambda aid,scope:{"people":[],"assets":[]})
    monkeypatch.setattr(missions.incident_simulation,"scan_enterprise_activity",lambda aid:{"findings":[],"checked_assets":14})
    monkeypatch.setattr(employee_commands,"workspace_state",lambda aid:[{"employee_id":"EMP-001"}])
    return state


def test_strict_agent_blocks_before_business_tools_when_model_offline(worker,monkeypatch):
    doc=missions.new_document(uuid4(),"Kiểm tra máy nhân viên","all","tester",mode="agent")
    worker["doc"]=doc
    def offline(*args):raise planner.PlannerBlocked("offline")
    monkeypatch.setattr(planner,"plan_with_model",offline)
    missions.run_mission("assessment",doc["mission_id"])
    final=worker["saved"][-1]
    assert final["status"]=="blocked" and all(task["status"]=="blocked" for task in final["tasks"])
    assert all("output" not in task for task in final["tasks"])
    assert final["error_code"]=="planner_unavailable"


def test_fallback_requires_explicit_option_and_is_logged(worker,monkeypatch):
    doc=missions.new_document(uuid4(),"Kiểm tra máy nhân viên","all","tester",mode="agent",allow_fallback=True)
    worker["doc"]=doc
    def offline(*args):raise planner.PlannerBlocked("offline")
    monkeypatch.setattr(planner,"plan_with_model",offline)
    missions.run_mission("assessment",doc["mission_id"])
    final=worker["saved"][-1]
    assert final["status"]=="awaiting_review" and final["review"] is None
    assert final["execution_source"]=="workflow-fallback"
    assert any(event["kind"]=="fallback" for event in final["trace"])


def test_agent_executes_validated_plan_and_preserves_memory_trace(worker,monkeypatch):
    doc=missions.new_document(uuid4(),"Kiểm tra máy nhân viên","hardware","tester",mode="agent")
    worker["doc"]=doc
    def plan(goal,scope,memory):
        assert memory[0]["mission_id"]=="reviewed-case"
        return {**valid_plan(),"scope":scope,"source":"ollama_plan_and_execute","model":"test-model"}
    monkeypatch.setattr(planner,"plan_with_model",plan)
    missions.run_mission("assessment",doc["mission_id"])
    final=worker["saved"][-1]
    assert final["status"]=="awaiting_review" and final["execution_source"]=="ollama_plan_and_execute"
    assert len(final["diagnostics"])==1 and final["diagnostics"][0]["workstations"]
    assert all(task["status"]=="completed" for task in final["tasks"])
    assert [event["tool"] for event in final["trace"] if event["kind"]=="dispatch"]==["inventory","workstations","security","report"]


def test_restart_preserves_completed_artifacts_but_stops_running_animation():
    doc=missions.new_document(uuid4(),"Kiểm tra máy nhân viên","all","tester")
    doc["tasks"][0].update(status="completed",output={"saved":"artifact"})
    doc["tasks"][1]["status"]="running"
    result=missions.interrupt_document(doc)
    assert result["status"]=="interrupted"
    assert result["tasks"][0]["output"]=={"saved":"artifact"}
    assert [task["status"] for task in result["tasks"]]==["completed","blocked","blocked","blocked"]


def test_review_hash_tracks_artifacts_and_not_animation_or_review_notes():
    doc=missions.new_document(uuid4(),"Kiểm tra máy nhân viên","all","tester")
    original=missions.artifact_hash(doc)
    doc["trace"].append({"kind":"progress"})
    doc["review"]={"note":"Nhận xét"}
    assert missions.artifact_hash(doc)==original
    doc["tasks"][1]["output"]={"assets":["OFFICE-EMP-001"]}
    assert missions.artifact_hash(doc)!=original


def test_case_budget_leaves_remaining_findings_as_review_blockers(worker,monkeypatch):
    doc=missions.new_document(uuid4(),"Kiểm tra dấu hiệu còn mở","hardware","tester")
    worker["doc"]=doc
    findings=[{"control_id":"A.7.10","event_id":str(i),"asset_id":"OFFICE-EMP-001","employee_id":"EMP-001"} for i in range(4)]
    processed=[]
    monkeypatch.setattr(missions.incident_simulation,"scan_enterprise_activity",lambda aid:{"checked_assets":14,"findings":findings[len(processed):]})
    def respond(aid,user,scan,emit):
        assert len(scan["findings"])==1
        finding=scan["findings"][0];processed.append(finding["event_id"])
        return [{"incident_id":finding["event_id"],"control_id":"A.7.10","verified":True,"model":"test"}]
    monkeypatch.setattr(incident_api,"_process_monitor_findings",respond)
    missions.run_mission("assessment",doc["mission_id"])
    final=worker["saved"][-1]
    assert len(processed)==3 and final["status"]=="awaiting_review"
    report=final["tasks"][-1]["output"]
    assert report["detected_count"]==4 and report["processed_count"]==3
    assert report["remaining_count"]==1 and report["blockers"]
