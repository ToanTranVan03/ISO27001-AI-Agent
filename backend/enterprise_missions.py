"""Persistent department handoffs over the existing synthetic ISO lab tools."""
import logging
from datetime import datetime, timezone

from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend import incident_simulation
from backend.incident_catalog import SCENARIO_BY_CONTROL

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
        cur.execute("""UPDATE enterprise_missions SET document=document ||
            '{"status":"interrupted","error":"Máy chủ đã khởi động lại. Tạo lượt kiểm tra mới để tiếp tục từ dữ liệu hiện tại."}'::jsonb
            WHERE document->>'status' IN ('queued','running')""")


def new_document(mission_id, goal, scope, user_id):
    return {"mission_id": str(mission_id), "goal": goal, "scope": scope, "submitted_by": user_id,
            "status": "queued", "created_at": now(), "is_synthetic": True,
            "execution_source": "bounded_department_workflow",
            "tasks": [{"id": key, "department": department, "title": title, "status": "waiting"}
                      for key, department, title in DEPARTMENTS], "handoffs": [], "review": None}


def list_missions(assessment_id):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT document FROM enterprise_missions WHERE assessment_id=%s ORDER BY created_at DESC LIMIT 10", (assessment_id,))
        return [row[0] for row in cur.fetchall()]


def create_mission(assessment_id, mission_id, goal, scope, user_id):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (f"mission-create:{assessment_id}",))
        cur.execute("SELECT document FROM enterprise_missions WHERE assessment_id=%s AND mission_id=%s", (assessment_id, mission_id))
        existing = cur.fetchone()
        if existing:
            doc = existing[0]
            if (doc["goal"], doc["scope"], doc["submitted_by"]) != (goal, scope, user_id):
                raise ValueError("Mã nhiệm vụ đã được dùng cho nội dung khác.")
            return doc, False
        cur.execute("SELECT 1 FROM enterprise_missions WHERE assessment_id=%s AND document->>'status' IN ('queued','running')", (assessment_id,))
        if cur.fetchone():
            raise ValueError("Các phòng đang thực hiện một nhiệm vụ. Chờ bàn giao xong rồi giao nhiệm vụ tiếp.")
        doc = new_document(mission_id, goal, scope, user_id)
        cur.execute("INSERT INTO enterprise_missions (assessment_id,mission_id,document) VALUES (%s,%s,%s)", (assessment_id, mission_id, Jsonb(doc)))
        return doc, True


def save(assessment_id, doc):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("UPDATE enterprise_missions SET document=%s WHERE assessment_id=%s AND mission_id=%s", (Jsonb(doc), assessment_id, doc["mission_id"]))


def in_scope(control_id, scope):
    return scope == "all" or SCENARIO_BY_CONTROL.get(control_id, {}).get("domain") == scope


def scoped_scan(scan, scope):
    return {**scan, "findings": [finding for finding in scan["findings"] if in_scope(finding["control_id"], scope)]}


def inventory_snapshot(assessment_id, scope):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT employee_id,display_name,department,job_title FROM enterprise_sim_people WHERE assessment_id=%s ORDER BY employee_id", (assessment_id,))
        people = [dict(zip(("employee_id", "name", "department", "role"), row)) for row in cur.fetchall()]
        cur.execute("SELECT asset_id,asset_type,asset_name,department FROM enterprise_sim_assets WHERE assessment_id=%s ORDER BY asset_id", (assessment_id,))
        assets = [dict(zip(("asset_id", "type", "name", "department"), row)) for row in cur.fetchall() if scope == "all" or row[1] == scope]
    return {"captured_at": now(), "people": people if scope in {"all", "people"} else [], "assets": assets,
            "source": "enterprise_sim_people / enterprise_sim_assets"}


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
            "limitation": "Dữ liệu doanh nghiệp giả lập. Không phát hiện dấu hiệu không đồng nghĩa đạt toàn bộ 56 kiểm soát ISO. Chủ đề là mô tả nhiệm vụ; các bước thực thi được giới hạn theo phạm vi đã chọn."}


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
        doc["status"] = "running"
        def step(index, operation):
            task = doc["tasks"][index]
            task.update(status="running", started_at=now())
            save(assessment_id, doc)
            task.update(output=operation(), status="completed", finished_at=now())
            doc["handoffs"].append({"from": task["department"], "to": doc["tasks"][index+1]["department"] if index < 3 else "Người phụ trách duyệt", "at": now()})
            save(assessment_id, doc)
            return task["output"]
        try:
            step(0, lambda: {"goal": doc["goal"], "scope": doc["scope"], "workflow": "inventory → security → report → human review"})
            step(1, lambda: inventory_snapshot(assessment_id, doc["scope"]))
            def audit():
                with _scan_lock(assessment_id):
                    scan = scoped_scan(incident_simulation.scan_enterprise_activity(assessment_id), doc["scope"])
                    reports = _process_monitor_findings(assessment_id, doc["submitted_by"], scan)
                return {"scan": scan, "reports": [{key: report.get(key) for key in
                    ("incident_id", "control_id", "verified", "model", "agent_rationale", "actions", "verification_checks", "evidence_id", "sha256_hash")}
                    for report in reports]}
            security = step(2, audit)
            def report():
                remaining = scoped_scan(incident_simulation.scan_enterprise_activity(assessment_id), doc["scope"])
                with get_connection() as con, con.cursor() as cursor:
                    cursor.execute("SELECT incident_id,control_id,status FROM enterprise_incidents WHERE assessment_id=%s AND status <> 'RESOLVED'", (assessment_id,))
                    unresolved = [{"incident_id": str(row[0]), "control_id": row[1], "status": row[2]} for row in cursor.fetchall() if in_scope(row[1], doc["scope"])]
                return build_report(security["scan"], security["reports"], remaining, unresolved)
            step(3, report)
            doc.update(status="awaiting_review", finished_at=now())
        except Exception as exc:
            logger.exception("Enterprise mission failed: %s", mission_id)
            for task in doc["tasks"]:
                if task["status"] == "running":
                    task.update(status="failed", error=type(exc).__name__)
                elif task["status"] == "waiting":
                    task["status"] = "blocked"
            doc.update(status="failed", error="Chưa hoàn tất bàn giao. Kiểm tra dịch vụ và tạo lượt kiểm tra mới.")
        save(assessment_id, doc)


def review_mission(assessment_id, mission_id, decision, note, user_id):
    with get_connection() as con, con.cursor() as cur:
        cur.execute("SELECT document FROM enterprise_missions WHERE assessment_id=%s AND mission_id=%s FOR UPDATE", (assessment_id, mission_id))
        row = cur.fetchone()
        if not row:
            raise LookupError("Không tìm thấy nhiệm vụ trong đợt đánh giá này.")
        doc = row[0]
        if doc["status"] != "awaiting_review":
            raise ValueError("Chỉ duyệt được nhiệm vụ đã hoàn tất các bước và đang chờ duyệt.")
        if decision == "approve" and doc["tasks"][-1]["output"]["blockers"]:
            raise ValueError("Hồ sơ còn hạng mục chưa xử lý; yêu cầu bổ sung và chạy kiểm tra lại.")
        if decision == "approve":
            fresh = scoped_scan(incident_simulation.scan_enterprise_activity(assessment_id), doc["scope"])
            cur.execute("SELECT control_id FROM enterprise_incidents WHERE assessment_id=%s AND status <> 'RESOLVED'", (assessment_id,))
            if fresh["findings"] or any(in_scope(row[0], doc["scope"]) for row in cur.fetchall()):
                raise ValueError("Dữ liệu đã có dấu hiệu hoặc hồ sơ chưa xử lý. Yêu cầu bổ sung và tạo lượt kiểm tra mới trước khi duyệt.")
        doc.update(status="approved" if decision == "approve" else "revision_requested", review={"decision": decision, "note": note, "reviewed_by": user_id, "at": now()})
        cur.execute("UPDATE enterprise_missions SET document=%s WHERE assessment_id=%s AND mission_id=%s", (Jsonb(doc), assessment_id, mission_id))
        return doc
