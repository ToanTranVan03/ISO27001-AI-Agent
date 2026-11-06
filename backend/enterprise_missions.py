"""Persistent department handoffs over the existing synthetic ISO lab tools."""
import logging
import time
import json
import hashlib
from datetime import datetime, timezone

from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend import incident_simulation
from backend.incident_catalog import SCENARIO_BY_CONTROL
from backend import mission_planner
from backend import mission_activity as activity
from backend import mission_targets as targets

logger = logging.getLogger(__name__)
DEPARTMENTS = [
    ("coordination", "Điều phối", "Xác định phạm vi và bàn giao"),
    ("inventory", "Tài sản & nhân sự", "Thu thập danh mục hiện có"),
    ("security", "SOC · ứng phó", "Quét telemetry và xử lý dấu hiệu"),
    ("report", "Kiểm soát nội bộ", "Đối chiếu kết quả, lập hồ sơ chờ duyệt"),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def initialize_missions():
    with get_connection() as con, con.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS enterprise_missions (
            assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id) ON DELETE CASCADE,
            mission_id UUID NOT NULL, document JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (assessment_id,mission_id))""")
        # A server restart cannot truthfully leave an in-process worker running.
        cur.execute("SELECT assessment_id,mission_id,document FROM enterprise_missions WHERE document->>'status' IN ('queued','running') FOR UPDATE")
        for assessment_id, mission_id, doc in cur.fetchall():
            interrupt_document(doc)
            cur.execute("UPDATE enterprise_missions SET document=%s WHERE mission_id=%s AND assessment_id=%s",
                        (Jsonb(doc), mission_id, assessment_id))


def interrupt_document(doc):
    doc.update(status="interrupted", error="Máy chủ đã khởi động lại. Tạo lượt kiểm tra mới từ dữ liệu hiện tại.")
    if doc.get("current_activity"):doc["current_activity"].update(active=False,state="interrupted")
    for task in doc["tasks"]:
        if task["status"] in {"running", "waiting"}:
            task["status"] = "blocked"
    doc.setdefault("trace", []).append({"at": now(), "kind": "interrupted", "tool": "runtime", "text": doc["error"]})
    activity.stop_subtasks(doc,"blocked",doc["error"])
    activity.add_message(doc,"coordination",doc["error"],"blocked")
    return doc


def new_document(mission_id, goal, scope, user_id, mode="workflow", allow_fallback=False, requested_role="coordination", target=None):
    doc = {"mission_id": str(mission_id), "goal": goal, "scope": scope, "submitted_by": user_id,
            "status": "queued", "created_at": now(), "is_synthetic": True,
            "execution_source": "pending", "mode": mode, "allow_fallback": allow_fallback,
            "trace": [], "memory": [], "diagnostics": [], "requested_role":requested_role,
            "subtasks":[], "agent_messages":[], "target":target, "current_activity":None,
            "tasks": [{"id": key, "department": department, "title": title, "status": "waiting"}
                      for key, department, title in DEPARTMENTS], "handoffs": [], "review": None}
    activity.add_subtask(doc,"coordination","Xác định phạm vi và chia công việc cho các phòng.")
    activity.add_message(doc,requested_role,f"Đã nhận yêu cầu. Điều phối sẽ chia việc trong phạm vi đã giao; {activity.ROLES[requested_role]} là vai trò tiếp nhận.","received")
    return doc


def list_missions(assessment_id):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT document FROM enterprise_missions WHERE assessment_id=%s ORDER BY created_at DESC LIMIT 10", (assessment_id,))
        return [row[0] for row in cur.fetchall()]


def create_mission(assessment_id, mission_id, goal, scope, user_id, mode="workflow", allow_fallback=False, requested_role="coordination", target=None):
    target=targets.resolve_target(assessment_id,target)
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (f"mission-create:{assessment_id}",))
        cur.execute("SELECT document FROM enterprise_missions WHERE assessment_id=%s AND mission_id=%s", (assessment_id, mission_id))
        existing = cur.fetchone()
        if existing:
            doc = existing[0]
            if targets.identity(doc.get("target"))!=targets.identity(target):
                raise ValueError("Mã nhiệm vụ đã được dùng cho người/máy hoặc sự kiện khác.")
            if (doc["goal"], doc["scope"], doc["submitted_by"], doc.get("mode", "workflow"), doc.get("allow_fallback", False), doc.get("requested_role","coordination")) != (goal, scope, user_id, mode, allow_fallback, requested_role):
                raise ValueError("Mã nhiệm vụ đã được dùng cho nội dung khác.")
            return doc, False
        cur.execute("SELECT 1 FROM enterprise_missions WHERE assessment_id=%s AND document->>'status' IN ('queued','running')", (assessment_id,))
        if cur.fetchone():
            raise ValueError("Các phòng đang thực hiện một nhiệm vụ. Chờ bàn giao xong rồi giao nhiệm vụ tiếp.")
        doc = new_document(mission_id, goal, scope, user_id, mode, allow_fallback, requested_role,target)
        cur.execute("INSERT INTO enterprise_missions (assessment_id,mission_id,document) VALUES (%s,%s,%s)", (assessment_id, mission_id, Jsonb(doc)))
        return doc, True


def save(assessment_id, doc):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("UPDATE enterprise_missions SET document=%s WHERE assessment_id=%s AND mission_id=%s", (Jsonb(doc), assessment_id, doc["mission_id"]))


def reviewed_memory(assessment_id, scope, target=None):
    """Bounded, assessment-scoped retrieval of reviewed outcomes, not model training."""
    with get_connection() as con, con.cursor() as cur:
        cur.execute("""SELECT document FROM enterprise_missions WHERE assessment_id=%s
            AND document->>'scope'=%s AND document->>'status' IN ('approved','revision_requested')
            AND (%s::text IS NULL OR document->'target'->>'asset_id'=%s)
            ORDER BY created_at DESC LIMIT 3""", (assessment_id, scope,(target or {}).get("asset_id"),(target or {}).get("asset_id")))
        return [{"mission_id": doc["mission_id"], "goal": doc["goal"][:600], "status": doc["status"],
                 "review_note": doc.get("review", {}).get("note", "")[:500],
                 "summary": doc["tasks"][-1].get("output", {}).get("summary", "")[:500]}
                for (doc,) in cur.fetchall()]


def artifact_hash(doc):
    payload={"goal": doc["goal"], "scope": doc["scope"],
             "outputs": [task.get("output") for task in doc["tasks"]],
             "diagnostics": doc.get("diagnostics", [])}
    if doc.get("target"):payload["target"]=targets.identity(doc["target"])
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",", ":")).encode("utf-8")).hexdigest()


def in_scope(control_id, scope):
    return scope == "all" or SCENARIO_BY_CONTROL.get(control_id, {}).get("domain") == scope


def scoped_scan(scan, scope, target=None):
    result={**scan, "findings": [finding for finding in scan["findings"] if in_scope(finding["control_id"], scope) and targets.matches(finding,target)]}
    if target:
        result.update(source_asset_count=scan.get("checked_assets",0),checked_assets=1,target=target,
                      recently_processed=[item for item in scan.get("recently_processed",[]) if item.get("asset_id")==target["asset_id"] and (not target.get("event_id") or item.get("event_id")==target["event_id"])])
    return result


def inventory_snapshot(assessment_id, scope, target=None):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT employee_id,display_name,department,job_title FROM enterprise_sim_people WHERE assessment_id=%s ORDER BY employee_id", (assessment_id,))
        people = [dict(zip(("employee_id", "name", "department", "role"), row)) for row in cur.fetchall()]
        cur.execute("SELECT asset_id,asset_type,asset_name,department FROM enterprise_sim_assets WHERE assessment_id=%s ORDER BY asset_id", (assessment_id,))
        assets = [dict(zip(("asset_id", "type", "name", "department"), row)) for row in cur.fetchall() if scope == "all" or row[1] == scope or (target and row[0]==target["asset_id"])]
    if target:
        people=[person for person in people if person["employee_id"]==target["employee_id"]]
        assets=[asset for asset in assets if asset["asset_id"]==target["asset_id"]]
    return {"captured_at": now(), "people": people if target or scope in {"all", "people"} else [], "assets": assets,
            "source": "enterprise_sim_people / enterprise_sim_assets"}


def unresolved_incidents(assessment_id,scope,target=None):
    with get_connection() as con,con.cursor() as cur:
        cur.execute("SELECT incident_id,control_id,status,event FROM enterprise_incidents WHERE assessment_id=%s AND status <> 'RESOLVED'",(assessment_id,))
        return [{"incident_id":str(row[0]),"control_id":row[1],"status":row[2]} for row in cur.fetchall()
                if in_scope(row[1],scope) and targets.incident_matches(row[3],target)]


def build_report(scan, reports, remaining, unresolved):
    blockers = []
    if remaining["findings"]:
        blockers.append(f"Còn {len(remaining['findings'])} dấu hiệu mới chưa xử lý trong phạm vi.")
    if any(not report.get("verified") for report in reports):
        blockers.append("Có kết quả xử lý chưa xác minh thành công.")
    if unresolved:
        blockers.append(f"Còn {len(unresolved)} hồ sơ sự cố chưa giải quyết trong phạm vi.")
    return {"captured_at": now(), "detected_count": len(scan["findings"]),
            "processed_count": len(reports), "remaining_count": len(remaining["findings"]),
            "incident_ids": [report["incident_id"] for report in reports],
            "unresolved_incidents": unresolved, "blockers": blockers,
            "summary": "Có hạng mục cần xử lý tiếp." if blockers else "Đã hoàn tất lượt kiểm tra dữ liệu hiện có; chờ người phụ trách duyệt hồ sơ.",
            "limitation": "Dữ liệu doanh nghiệp giả lập. Không phát hiện dấu hiệu không đồng nghĩa đạt toàn bộ 56 kiểm soát ISO. Kế hoạch chỉ sử dụng công cụ được cho phép trong phạm vi đã chọn; checklist của AI chưa phải kết quả xác minh."}


def run_mission(assessment_id, mission_id):
    # Reuse the monitor's lock/tools so two scanners do not process the same event.
    from backend.incident_api import _scan_lock, _process_monitor_findings
    with get_connection() as claim, claim.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0))", (f"mission-run:{assessment_id}:{mission_id}",))
        if not cur.fetchone()[0]:
            return
        cur.execute("SELECT document FROM enterprise_missions WHERE assessment_id=%s AND mission_id=%s", (assessment_id, mission_id))
        row = cur.fetchone()
        if not row or row[0]["status"] != "queued":
            return
        doc = row[0]
        if not doc.get("subtasks"):
            activity.add_subtask(doc,"coordination","Lập kế hoạch và chia việc.")
        doc["status"] = "running"
        started = time.monotonic()
        def trace(kind, tool, text, **extra):
            doc.setdefault("trace", []).append({"at": now(), "kind": kind, "tool": tool, "text": text, **extra})
            save(assessment_id, doc)
        def step(index, operation):
            task = doc["tasks"][index]
            task.update(status="running", started_at=now())
            activity.start_subtask(doc,task["id"])
            trace("tool_started", task["id"], task["title"])
            tick = time.monotonic()
            task.update(output=operation(), status="completed", finished_at=now())
            activity.finish_subtask(doc,task["id"],task["output"],f"tasks.{index}.output")
            doc["handoffs"].append({"from": task["department"], "to": doc["tasks"][index+1]["department"] if index < 3 else "Người phụ trách duyệt", "at": now()})
            trace("tool_completed", task["id"], "Đã lưu đầu ra thực tế", elapsed_ms=round((time.monotonic()-tick)*1000))
            return task["output"]
        try:
            def planning():
                if doc.get("mode", "workflow") == "workflow":
                    return mission_planner.workflow_plan(doc["goal"], doc["scope"])
                doc["memory"] = reviewed_memory(assessment_id, doc["scope"],doc["target"]) if doc.get("target") else reviewed_memory(assessment_id,doc["scope"])
                trace("memory_loaded", "coordination", f"Đã đọc {len(doc['memory'])} hồ sơ đã có nhận xét trong phạm vi.")
                try:
                    if doc.get("target"):
                        return mission_planner.plan_with_model(doc["goal"],doc["scope"],doc["memory"],requested_role=doc.get("requested_role","coordination"),target=doc["target"])
                    if doc.get("requested_role","coordination")=="coordination":
                        return mission_planner.plan_with_model(doc["goal"], doc["scope"], doc["memory"])
                    return mission_planner.plan_with_model(doc["goal"], doc["scope"], doc["memory"], requested_role=doc["requested_role"])
                except mission_planner.PlannerBlocked as exc:
                    if not doc.get("allow_fallback"):
                        raise
                    trace("fallback", "coordination", str(exc), error_code=exc.code)
                    return {**mission_planner.workflow_plan(doc["goal"], doc["scope"]), "source": "workflow-fallback", "fallback_reason": str(exc)}
            plan = step(0, planning)
            for entry in plan["steps"]:
                activity.add_subtask(doc,entry["tool"],entry["purpose"])
            first_role=activity.TOOL_ROLES[plan["steps"][0]["tool"]]
            activity.add_message(doc,"coordination",f"Kế hoạch đã sẵn sàng. Giao bước đầu cho {activity.ROLES[first_role]}.","handoff","coordination",f"{doc['mission_id']}:artifact:coordination",to_role=first_role)
            doc["execution_source"] = plan["source"]
            trace("plan_ready", "coordination", plan["objective"], model=plan["model"])
            def audit():
                doc["current_activity"]={**(doc.get("target") or {}),"state":"scanning","active":True,"at":now(),"mission_id":doc["mission_id"]}
                trace("target_scan","security","SOC đang kiểm tra mục tiêu đã giao.")
                lock = _scan_lock(assessment_id)
                if not lock.acquire(timeout=15):
                    raise mission_planner.PlannerBlocked("SOC đang bận với lượt quét khác; tạo lượt mới sau khi hoàn tất.", "scanner_busy")
                try:
                    scan = scoped_scan(incident_simulation.scan_enterprise_activity(assessment_id), doc["scope"],doc.get("target"))
                    reports = []
                    for finding in scan["findings"][:3]:
                        if time.monotonic()-started > 240:
                            break
                        doc["current_activity"]={key:finding.get(key) for key in ("employee_id","asset_id","event_id")}
                        doc["current_activity"].update(state="processing",active=True,at=now(),mission_id=doc["mission_id"])
                        trace("finding_target","security",f"SOC đang xử lý {finding.get('employee_id')} tại {finding['asset_id']}.")
                        def progress(event):
                            if event.get("type") in {"finding_detected", "tool_call_completed", "verification", "evidence_saved"}:
                                activity.add_message(doc,"security",event.get("text",event["type"])[:500],"progress","security")
                                trace("soc_progress", "security", event.get("text", event["type"])[:500])
                        results=_process_monitor_findings(assessment_id, doc["submitted_by"], {**scan, "findings": [finding]}, progress)
                        for result in results:
                            result.update(employee_id=finding.get("employee_id"),asset_id=finding["asset_id"],event_id=finding["event_id"])
                        reports.extend(results)
                        if results:
                            doc["current_activity"].update(state="verified" if results[-1].get("verified") else "needs_review",active=False,incident_id=results[-1]["incident_id"],at=now())
                            trace("target_result","security","Đã lưu kết quả gắn đúng người, máy và sự kiện.")
                    previous=targets.processed_events(assessment_id,doc.get("target"),doc["scope"])
                    new_ids={item["incident_id"] for item in reports}
                    previous=[item for item in previous if item["incident_id"] not in new_ids]
                    if not reports:
                        record=previous[0] if previous else (doc.get("target") or {})
                        doc["current_activity"]={**record,"state":"already_processed" if previous else "no_findings","active":False,"at":now(),"mission_id":doc["mission_id"]}
                        if previous:activity.add_message(doc,"security",f"Sự kiện đã được xử lý trước lượt này. Đã liên kết {len(previous)} hồ sơ có sẵn.","previous_result","security")
                finally:
                    lock.release()
                return {"scan": scan, "previously_processed":previous,"reports": [{key: report.get(key) for key in
                    ("incident_id", "control_id", "verified", "model", "agent_rationale", "actions", "verification_checks", "evidence_id", "sha256_hash","employee_id","asset_id","event_id")}
                    for report in reports]}
            security = None
            def report():
                remaining = scoped_scan(incident_simulation.scan_enterprise_activity(assessment_id), doc["scope"],doc.get("target"))
                unresolved = unresolved_incidents(assessment_id,doc["scope"],doc.get("target"))
                return build_report(security["scan"], security["reports"], remaining, unresolved)
            for entry in plan["steps"]:
                if time.monotonic()-started > 240:
                    raise mission_planner.PlannerBlocked("Đã hết ngân sách thời gian giữa các bước. Tạo lượt mới từ dữ liệu hiện tại.", "time_budget")
                tool = entry["tool"]
                trace("dispatch", tool, entry["purpose"])
                if tool == "inventory":
                    step(1, lambda: inventory_snapshot(assessment_id, doc["scope"],doc["target"]) if doc.get("target") else inventory_snapshot(assessment_id,doc["scope"]))
                elif tool == "workstations":
                    from backend.employee_commands import workspace_state
                    activity.start_subtask(doc,tool)
                    trace("tool_started", tool, "Đọc trạng thái máy trong doanh nghiệp giả lập")
                    # Workstation diagnostics belong to hardware or all scopes only.
                    machines = workspace_state(assessment_id) if doc["scope"] in {"all", "hardware"} or doc.get("target") else []
                    if doc.get("target"):machines=[item for item in machines if item["employee_id"]==doc["target"]["employee_id"] and item["asset_id"]==doc["target"]["asset_id"]]
                    doc["diagnostics"].append({"tool": tool, "captured_at": now(), "scope": doc["scope"], "workstations": machines})
                    activity.finish_subtask(doc,tool,doc["diagnostics"][-1],f"diagnostics.{len(doc['diagnostics'])-1}")
                    trace("tool_completed", tool, f"Đã đọc {len(machines)} máy trong phạm vi.")
                elif tool == "security":
                    security = step(2, audit)
                elif tool == "report":
                    step(3, report)
            doc.update(status="awaiting_review", finished_at=now(), artifact_hash=artifact_hash(doc))
            activity.add_message(doc,"report","Đã lưu bộ đầu ra. Hồ sơ đang chờ bạn xem xét và duyệt.","awaiting_review","report",f"{doc['mission_id']}:artifact:report")
            trace("awaiting_review", "report", "Hoàn tất kiểm tra, chờ người phụ trách duyệt.")
        except mission_planner.PlannerBlocked as exc:
            if doc.get("current_activity"):doc["current_activity"].update(active=False,state="blocked")
            for task in doc["tasks"]:
                if task["status"] in {"running", "waiting"}:
                    task["status"] = "blocked"
            doc.update(status="blocked", error=str(exc), error_code=exc.code)
            activity.stop_subtasks(doc,"blocked",str(exc))
            activity.add_message(doc,"coordination",str(exc),"blocked")
            trace("blocked", "runtime", str(exc), error_code=exc.code)
        except Exception as exc:
            if doc.get("current_activity"):doc["current_activity"].update(active=False,state="failed")
            logger.exception("Enterprise mission failed: %s", mission_id)
            for task in doc["tasks"]:
                if task["status"] == "running":
                    task.update(status="failed", error=type(exc).__name__)
                elif task["status"] == "waiting":
                    task["status"] = "blocked"
            doc.update(status="failed", error="Chưa hoàn tất bàn giao. Kiểm tra dịch vụ và tạo lượt kiểm tra mới.")
            activity.stop_subtasks(doc,"failed",doc["error"])
            activity.add_message(doc,"coordination",doc["error"],"failed")
            trace("failed", "runtime", doc["error"], error_code=type(exc).__name__)
        doc["elapsed_ms"] = round((time.monotonic()-started)*1000)
        save(assessment_id, doc)


def review_mission(assessment_id, mission_id, decision, note, user_id, expected_hash=None):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT document FROM enterprise_missions WHERE assessment_id=%s AND mission_id=%s FOR UPDATE", (assessment_id, mission_id))
        row = cur.fetchone()
        if not row:
            raise LookupError("Không tìm thấy nhiệm vụ trong đợt đánh giá này.")
        doc = row[0]
        if doc["status"] != "awaiting_review":
            raise ValueError("Chỉ duyệt được nhiệm vụ đã hoàn tất các bước và đang chờ duyệt.")
        if doc.get("artifact_hash") and (expected_hash != doc["artifact_hash"] or artifact_hash(doc) != doc["artifact_hash"]):
            raise ValueError("Phiên bản hồ sơ chưa khớp. Tải lại hồ sơ trước khi nhận xét hoặc duyệt.")
        if decision == "approve" and doc["tasks"][-1]["output"]["blockers"]:
            raise ValueError("Hồ sơ còn hạng mục chưa xử lý; yêu cầu bổ sung và chạy kiểm tra lại.")
        if decision == "approve":
            fresh = scoped_scan(incident_simulation.scan_enterprise_activity(assessment_id), doc["scope"],doc.get("target"))
            if fresh["findings"] or unresolved_incidents(assessment_id,doc["scope"],doc.get("target")):
                raise ValueError("Dữ liệu đã có dấu hiệu hoặc hồ sơ chưa xử lý. Yêu cầu bổ sung và tạo lượt kiểm tra mới trước khi duyệt.")
        doc.update(status="approved" if decision == "approve" else "revision_requested", review={"decision": decision, "note": note, "reviewed_by": user_id, "at": now()})
        activity.add_message(doc,"report","Người phụ trách đã duyệt hồ sơ." if decision=="approve" else "Người phụ trách yêu cầu bổ sung: "+note,"review_saved","report")
        cur.execute("UPDATE enterprise_missions SET document=%s WHERE assessment_id=%s AND mission_id=%s", (Jsonb(doc), assessment_id, mission_id))
        return doc
