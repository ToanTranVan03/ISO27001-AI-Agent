"""Bounded chat commands for fictional employees; never execute host commands."""
import unicodedata
import re
from datetime import datetime
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend.incident_catalog import SCENARIOS
from backend.office_logic import DEFAULT_STATE, RISK_EVENTS, transition, lock_key, preparation_steps


ACTORS = {scenario["human_context"]["employee_id"]: {
    "asset_id": scenario["target"]["asset_id"], "host_asset_id": scenario["target"]["asset_id"], "room": scenario["domain"]
} for scenario in reversed(SCENARIOS)}
ACTORS.update({
    "EMP-006": {"asset_id": "USB-OPS-07", "host_asset_id": "WS-FIN-02", "room": "hardware"},
    "EMP-025": {"asset_id": "SRV-APP-02", "host_asset_id": "SRV-APP-02", "room": "software"},
})
ACTORS = {employee_id: {"asset_id": f"OFFICE-{employee_id}", "host_asset_id": f"OFFICE-{employee_id}", "room": "hardware"}
          for employee_id in [f"EMP-{i:03}" for i in range(1, 51)]}
COMMANDS = {
    "/di-lam": {"aliases": ["di lam", "tham gia", "vao van phong"], "event_type": "approved_work_session",
                 "label": "Đi làm · tham gia bằng một lệnh", "employee_id": None},
    "/vao-ca": {"aliases": ["vao ca", "cham cong"], "event_type": "employee_shift_started",
                 "label": "Vào ca tại văn phòng", "employee_id": None},
    "/nghi": {"aliases": ["nghi", "nghi giai lao"], "event_type": "approved_break_started",
               "label": "Khóa máy và nghỉ giải lao", "employee_id": None},
    "/khoa-may": {"aliases": ["khoa may", "khoa man hinh"], "event_type": "screen_locked_by_employee",
                   "label": "Khóa màn hình làm việc", "employee_id": None},
    "/roi-may": {"aliases": ["roi may", "roi may khong khoa", "bo may khong khoa"], "event_type": "unattended_screen_unlocked",
                  "label": "Rời bàn, giữ nguyên màn hình", "employee_id": None},
    "/lam-viec": {"aliases": ["lam viec", "lam viec binh thuong", "quay lai", "ve ban"], "event_type": "approved_work_session",
                   "label": "Làm việc theo quy trình", "employee_id": None},
    "/usb-la": {"aliases": ["cam usb la", "cam usb chua dang ky"], "event_type": "unapproved_usb_inserted",
                "label": "Cắm USB chưa đăng ký", "employee_id": None},
    "/cai-app-la": {"aliases": ["cai app la", "cai phan mem la", "cai phan mem chua duyet"],
                    "event_type": "unapproved_software_installed", "label": "Cài phần mềm chưa duyệt", "employee_id": None},
    "/rut-usb": {"aliases": ["rut usb"], "event_type": "usb_removed_by_employee", "label": "Rút USB", "employee_id": None},
    "/go-app": {"aliases": ["go app", "go phan mem la"], "event_type": "software_removed_by_employee", "label": "Gỡ ứng dụng lạ", "employee_id": None},
    "/mo-khoa": {"aliases": ["mo khoa", "mo khoa may"], "event_type": "workstation_reopened_after_review", "label": "Mở lại máy sau kiểm tra", "employee_id": None},
    "/tan-ca": {"aliases": ["tan ca", "ve nha"], "event_type": "employee_shift_ended", "label": "Tan ca", "employee_id": None},
}


def initialize_workstations():
    """Add a dedicated fictional workstation for each employee; preserve existing state."""
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""INSERT INTO enterprise_sim_assets (assessment_id,asset_id,asset_type,asset_name,department,state)
                SELECT assessment_id,'OFFICE-'||employee_id,'hardware','Máy làm việc '||employee_id,department,%s
                FROM enterprise_sim_people ON CONFLICT DO NOTHING""", (Jsonb(DEFAULT_STATE),))
            cur.execute("""INSERT INTO enterprise_sim_asset_people (assessment_id,asset_id,employee_id,relationship)
                SELECT assessment_id,'OFFICE-'||employee_id,employee_id,'responsible_employee'
                FROM enterprise_sim_people ON CONFLICT DO NOTHING""")


def parse_command(text: str, employee_id: str) -> tuple[str, dict]:
    if employee_id not in ACTORS:
        raise ValueError("Chọn nhân viên trong danh sách diễn tập.")
    mention = re.match(r"^@?(EMP-\d{3})\s+(.+)$", text.strip(), flags=re.I)
    if mention:
        if mention[1].upper() != employee_id:
            raise ValueError("Nhân viên được nhắc trong lệnh không khớp người nhận.")
        text = mention[2]
    normalized = " ".join("".join(c for c in unicodedata.normalize("NFD", text.lower().strip())
                                 if unicodedata.category(c) != "Mn").replace("đ", "d").split())
    for key, spec in COMMANDS.items():
        if normalized in [key, *spec["aliases"]]:
            if spec["employee_id"] and spec["employee_id"] != employee_id:
                raise ValueError(f"Lệnh này dùng cho {spec['employee_id']} và thiết bị được phân công.")
            return key, spec
    raise ValueError("Chưa hiểu lệnh. Chọn một lệnh gợi ý bên dưới; mỗi bình luận chỉ chứa một lệnh.")


def execute_command(assessment_id: str, employee_id: str, text: str, request_id: UUID, user_id: str) -> dict:
    command, spec = parse_command(text, employee_id)
    actor = dict(ACTORS[employee_id])
    if spec.get("asset_id"):
        actor.update(asset_id=spec["asset_id"], host_asset_id=spec["asset_id"], room=spec["room"])
    event_id = f"CMD-{request_id}"
    with get_connection() as con:
        with con.cursor() as cur:
            # One command/event even if a lost HTTP response is retried.
            cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (assessment_id + event_id,))
            cur.execute("""SELECT details FROM enterprise_sim_asset_activity
                WHERE assessment_id=%s AND event_id=%s""", (assessment_id, event_id))
            existing = cur.fetchone()
            if existing:
                receipt = existing[0]["command_receipt"]
                if (receipt["employee_id"], receipt["command"], receipt["submitted_by"]) != (employee_id, command, user_id):
                    raise ValueError("Mã gửi lệnh đã được dùng cho nội dung khác.")
                return receipt
            cur.execute("SELECT pg_try_advisory_xact_lock(hashtextextended(%s, 0))", (lock_key(assessment_id, employee_id),))
            if not cur.fetchone()[0]:
                raise ValueError("Agent đang xử lý máy của nhân viên này. Hãy chờ kết quả trước khi gửi lệnh tiếp.")
            cur.execute("""SELECT person.display_name FROM enterprise_sim_asset_people link
                JOIN enterprise_sim_people person ON person.assessment_id=link.assessment_id AND person.employee_id=link.employee_id
                WHERE link.assessment_id=%s AND link.asset_id=%s AND link.employee_id=%s LIMIT 1""",
                (assessment_id, actor["asset_id"], employee_id))
            person = cur.fetchone()
            if person is None:
                raise ValueError("Không tìm thấy nhân viên và tài sản trong đợt đánh giá này.")
            cur.execute("SELECT state FROM enterprise_sim_assets WHERE assessment_id=%s AND asset_id=%s FOR UPDATE",
                        (assessment_id, actor["asset_id"]))
            before = cur.fetchone()[0]
            cur.execute("""SELECT COUNT(*) FROM enterprise_sim_asset_activity
                WHERE assessment_id=%s AND asset_id=%s AND details ? 'command_receipt'
                AND event_type=ANY(%s) AND details->>'triaged_by_incident' IS NULL""",
                (assessment_id, actor["asset_id"], list(RISK_EVENTS)))
            after, event_type = transition(command, before, cur.fetchone()[0])
            observed_at = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
            summary = f"{person[0]} ({employee_id}) thực hiện: {spec['label']} tại {actor['host_asset_id']} (giả lập)."
            receipt = {
                "event_id": event_id, "command": command, "text": text.strip(), "employee_id": employee_id,
                "employee_name": person[0], "event_type": event_type, **actor,
                "summary": summary, "observed_at": observed_at.isoformat(), "submitted_by": user_id,
                "is_synthetic": True, "before_state": {key: before.get(key, val) for key,val in DEFAULT_STATE.items()},
                "after_state": {key: after[key] for key in DEFAULT_STATE},
            }
            details = {"employee_id": employee_id, "host_asset_id": actor["host_asset_id"],
                       "command_receipt": receipt, "is_synthetic": True}
            if command == "/usb-la":
                details.update(device_class="removable_storage", approval_status="unregistered")
            elif command == "/cai-app-la":
                details.update(package_name="RemoteAssist-Portable", approval_status="unapproved", source="unknown_download")
            elif command == "/roi-may":
                details.update(screen_locked=after["screen_state"]=="locked", user_present=False, visible_data="customer_records")
            else:
                details.update(approval_status="approved")
                if command in {"/nghi", "/khoa-may"}:
                    details.update(screen_locked=True)
            cur.execute("""INSERT INTO enterprise_sim_asset_activity
                (assessment_id,asset_id,event_id,observed_at,event_type,source_system,summary,details)
                VALUES (%s,%s,%s,%s,%s,'SIMULATED_ENDPOINT_TELEMETRY',%s,%s)""",
                (assessment_id, actor["asset_id"], event_id, observed_at, event_type, summary, Jsonb(details)))
            after["last_receipt"] = receipt
            cur.execute("UPDATE enterprise_sim_assets SET state=%s,updated_at=NOW() WHERE assessment_id=%s AND asset_id=%s",
                        (Jsonb(after), assessment_id, actor["asset_id"]))
            return receipt


def execute_prepared_command(assessment_id, employee_id, text, request_id, user_id):
    """One comment can approach the desk first; every step remains durable and guarded."""
    command,_=parse_command(text,employee_id)
    event_id=f'CMD-{request_id}'
    with get_connection() as con, con.cursor() as cur:
        def read_preparation():
            event_ids=[f'CMD-{uuid5(request_id,"prepare:"+step)}' for step in ('/di-lam','/lam-viec')]
            cur.execute('''SELECT event_id,details->'command_receipt'->>'command' FROM enterprise_sim_asset_activity
                WHERE assessment_id=%s AND event_id=ANY(%s) ORDER BY observed_at''',(assessment_id,event_ids))
            return [{'command':row[1],'event_id':row[0]} for row in cur.fetchall()]
        cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(f'prepared:{assessment_id}:{request_id}',))
        cur.execute('SELECT details FROM enterprise_sim_asset_activity WHERE assessment_id=%s AND event_id=%s',
                    (assessment_id,event_id))
        if cur.fetchone():
            # Base executor validates the same person/command/user on every retry.
            result=execute_command(assessment_id,employee_id,text,request_id,user_id)
            return {**result,'preparation':read_preparation()}
        asset_id=f'OFFICE-{employee_id}'
        cur.execute('SELECT state FROM enterprise_sim_assets WHERE assessment_id=%s AND asset_id=%s',(assessment_id,asset_id))
        found=cur.fetchone()
        if not found:raise ValueError('Không tìm thấy máy của nhân viên trong đợt đánh giá.')
        cur.execute('''SELECT COUNT(*) FROM enterprise_sim_asset_activity WHERE assessment_id=%s AND asset_id=%s
            AND event_type=ANY(%s) AND details ? 'command_receipt' AND details->>'triaged_by_incident' IS NULL''',
                    (assessment_id,asset_id,list(RISK_EVENTS)))
        steps=preparation_steps(command,found[0],cur.fetchone()[0])
        prepared=[]
        for step in steps:
            receipt=execute_command(assessment_id,employee_id,step,uuid5(request_id,'prepare:'+step),user_id)
            prepared.append({'command':step,'event_id':receipt['event_id']})
        result=execute_command(assessment_id,employee_id,text,request_id,user_id)
        # Receipts are already durable. Do not rewrite the asset/event here while
        # the independent SOC may be locking them in the opposite order.
        return {**result,'preparation':prepared}


def workspace_state(assessment_id):
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""SELECT link.employee_id,asset.asset_id,asset.state,
                (SELECT COUNT(*) FROM enterprise_sim_asset_activity a WHERE a.assessment_id=asset.assessment_id
                 AND a.asset_id=asset.asset_id AND a.details ? 'command_receipt' AND a.event_type=ANY(%s)
                 AND a.details->>'triaged_by_incident' IS NULL)
                FROM enterprise_sim_assets asset JOIN enterprise_sim_asset_people link
                ON link.assessment_id=asset.assessment_id AND link.asset_id=asset.asset_id
                WHERE asset.assessment_id=%s AND asset.asset_id LIKE 'OFFICE-%%' ORDER BY link.employee_id""",
                (list(RISK_EVENTS), assessment_id))
            result=[]
            for employee_id,asset_id,state,pending in cur.fetchall():
                receipt=state.get("last_receipt")
                if receipt:
                    cur.execute("""SELECT i.incident_id,i.control_id,i.status,i.model_name
                        FROM enterprise_sim_asset_activity a JOIN enterprise_incidents i
                        ON i.assessment_id=a.assessment_id AND i.incident_id::text=a.details->>'triaged_by_incident'
                        WHERE a.assessment_id=%s AND a.asset_id=%s AND a.event_id=%s""",
                        (assessment_id,asset_id,receipt["event_id"]))
                    linked=cur.fetchone()
                    if linked:
                        state["last_receipt"]={**receipt,"incident_id":str(linked[0]),"detected_control":linked[1],"verified":linked[2]=="RESOLVED","model":linked[3]}
                actions=[]
                for command,spec in COMMANDS.items():
                    try:
                        transition(command,state,pending)
                        reason=None
                    except ValueError as exc:
                        reason=str(exc)
                    try:
                        preparation_steps(command,state,pending)
                        prepared_reason=None
                    except ValueError as exc:
                        prepared_reason=str(exc)
                    actions.append({"command":command,"label":spec["label"],"enabled":reason is None,"reason":reason,
                                    "prepared_enabled":prepared_reason is None,"prepared_reason":prepared_reason,
                                    "risk":command in {"/roi-may","/usb-la","/cai-app-la"}})
                result.append({"employee_id":employee_id,"asset_id":asset_id,"state":state,"pending_count":pending,"actions":actions})
            return result


def execute_office_command(assessment_id, action, request_id, user_id):
    """Fan out safe commands using the same per-person guards and durable receipts."""
    commands = {"start_shift": "/lam-viec", "work": "/lam-viec", "break": "/nghi", "end_shift": "/tan-ca"}
    if action not in commands:
        raise ValueError("Lệnh toàn công ty không hợp lệ.")
    results = []
    for machine in workspace_state(assessment_id):
        employee_id = machine["employee_id"]
        steps = [commands[action]]
        if action == "start_shift" and machine["state"]["shift"] == "off":
            steps.insert(0, "/vao-ca")
        receipts = []
        try:
            for command in steps:
                child_id = uuid5(request_id, f"{action}:{employee_id}:{command}")
                receipts.append(execute_command(assessment_id, employee_id, command, child_id, user_id))
            results.append({"employee_id": employee_id, "ok": True, "receipts": receipts})
        except ValueError as exc:
            results.append({"employee_id": employee_id, "ok": False, "reason": str(exc), "receipts": receipts})
    return {"results": results, "workspace": workspace_state(assessment_id), "entries": command_history(assessment_id)}


def command_catalog() -> dict:
    return {"actors": [{"employee_id": key, **value} for key, value in ACTORS.items()],
            "commands": [{"command": key, "label": value["label"], "employee_id": value["employee_id"],
                          "event_type": value["event_type"], "aliases": value["aliases"]} for key, value in COMMANDS.items()]}


def command_history(assessment_id: str) -> list[dict]:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""SELECT activity.details->'command_receipt', activity.details->>'triaged_by_incident',
                incident.control_id, incident.status='RESOLVED', incident.model_name
                FROM enterprise_sim_asset_activity activity
                LEFT JOIN enterprise_incidents incident ON incident.assessment_id=activity.assessment_id
                    AND incident.incident_id::text=activity.details->>'triaged_by_incident'
                WHERE activity.assessment_id=%s AND activity.details ? 'command_receipt'
                ORDER BY activity.observed_at DESC LIMIT 30""", (assessment_id,))
            return [{**row[0], "incident_id": row[1], "detected_control": row[2], "verified": row[3], "model": row[4]} for row in cur.fetchall()]
