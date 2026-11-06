from uuid import uuid4
from backend import enterprise_missions as missions, mission_activity as activity


def test_request_receives_chosen_role_but_no_fake_completed_work():
    doc=missions.new_document(uuid4(),"Kiểm tra USB","hardware","tester",requested_role="security")
    assert doc["requested_role"]=="security"
    assert doc["agent_messages"][0]["role"]=="security"
    assert doc["agent_messages"][0]["kind"]=="received"
    assert [task["status"] for task in doc["subtasks"]]==["waiting"]
    assert all("artifact_id" not in task for task in doc["subtasks"])


def test_only_completed_tool_creates_artifact_and_verified_counts():
    doc=missions.new_document(uuid4(),"Kiểm tra USB","hardware","tester")
    sub=activity.add_subtask(doc,"security","Quét USB")
    activity.start_subtask(doc,"security")
    assert sub["status"]=="running" and "artifact_id" not in sub
    output={"scan":{"findings":[{},{}]},"reports":[{"verified":True},{"verified":False}]}
    activity.finish_subtask(doc,"security",output,"tasks.2.output")
    assert sub["status"]=="completed" and sub["output_ref"]=="tasks.2.output"
    assert "xác minh thành công 1" in sub["summary"]
    assert doc["agent_messages"][-1]["artifact_id"]==sub["artifact_id"]


def test_stopped_job_cannot_leave_agent_working_or_fabricate_artifact():
    doc=missions.new_document(uuid4(),"Kiểm tra USB","hardware","tester")
    activity.start_subtask(doc,"coordination")
    activity.add_subtask(doc,"security","Quét USB")
    activity.stop_subtasks(doc,"failed","Model unavailable")
    assert [item["status"] for item in doc["subtasks"]]==["failed","blocked"]
    assert all("artifact_id" not in item for item in doc["subtasks"])


def test_handoff_links_saved_artifact_and_actual_next_role():
    doc=missions.new_document(uuid4(),"Kiểm tra USB","hardware","tester")
    activity.add_subtask(doc,"inventory","Đọc danh mục")
    activity.add_subtask(doc,"security","Quét USB")
    activity.start_subtask(doc,"inventory")
    activity.finish_subtask(doc,"inventory",{"people":[{}],"assets":[{},{}]},"tasks.1.output")
    handoff=doc["agent_messages"][-1]
    assert handoff["kind"]=="handoff" and handoff["to_role"]=="security"
    assert handoff["artifact_id"].endswith(":inventory")
    assert "1 hồ sơ nhân sự và 2 tài sản" in doc["subtasks"][1]["summary"]
