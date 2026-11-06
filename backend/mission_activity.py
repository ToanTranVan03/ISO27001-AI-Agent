"""User-facing activity derived from persisted tool outcomes, never simulated chat."""
from datetime import datetime, timezone

ROLES = {"coordination":"Điều phối", "inventory":"Tài sản & nhân sự", "security":"SOC · ứng phó", "report":"Kiểm soát nội bộ"}
TOOL_ROLES = {"coordination":"coordination", "inventory":"inventory", "workstations":"inventory", "security":"security", "report":"report"}
TITLES = {"coordination":"Lập kế hoạch và chia việc", "inventory":"Thu thập danh mục", "workstations":"Kiểm tra trạng thái máy", "security":"Quét, xử lý và xác minh", "report":"Lập hồ sơ bàn giao"}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def add_message(doc, role, text, kind="feedback", tool=None, artifact_id=None, source="runtime", to_role=None):
    rows = doc.setdefault("agent_messages", [])
    rows.append({"id":f"{doc['mission_id']}:message:{len(rows)+1}", "role":role, "text":text,
                 "kind":kind, "tool":tool, "artifact_id":artifact_id, "source":source, "at":timestamp(), "to_role":to_role})


def add_subtask(doc, tool, purpose):
    item={"id":f"{doc['mission_id']}:{tool}", "tool":tool, "role":TOOL_ROLES[tool],
          "title":TITLES[tool], "purpose":purpose, "status":"waiting", "created_at":timestamp()}
    doc.setdefault("subtasks", []).append(item)
    return item


def start_subtask(doc, tool):
    item=next(item for item in doc["subtasks"] if item["tool"]==tool)
    item.update(status="running", started_at=timestamp())
    add_message(doc,item["role"],f"Bắt đầu: {item['title'].lower()}.","started",tool)
    return item


def outcome_summary(tool, output):
    if tool=="coordination":return f"Đã lập {len(output.get('steps',[]))} công việc con. Nguồn lập kế hoạch: {output.get('model') or output.get('source','quy trình')}."
    if tool=="inventory":return f"Đã thu thập {len(output.get('people',[]))} hồ sơ nhân sự và {len(output.get('assets',[]))} tài sản, {len(output.get('accounts',[]))} tài khoản."
    if tool=="workstations":
        rows=output.get("workstations",[])
        isolated=sum(bool(item.get("state",{}).get("network_isolated")) for item in rows)
        return f"Đã đọc {len(rows)} máy; {isolated} máy đang cô lập mạng."
    if tool=="security":
        reports=output.get("reports",[]);verified=sum(bool(item.get("verified")) for item in reports)
        return f"Đã phát hiện {len(output.get('scan',{}).get('findings',[]))} dấu hiệu; xử lý {len(reports)}, xác minh thành công {verified}."
    return output.get("summary","Đã lưu hồ sơ bàn giao.")


def finish_subtask(doc, tool, output, output_ref):
    item=next(item for item in doc["subtasks"] if item["tool"]==tool)
    item.update(status="completed",finished_at=timestamp(),output_ref=output_ref,
                artifact_id=f"{doc['mission_id']}:artifact:{tool}",summary=outcome_summary(tool,output))
    add_message(doc,item["role"],item["summary"],"completed",tool,item["artifact_id"])
    index=doc["subtasks"].index(item)
    next_item=doc["subtasks"][index+1] if index+1<len(doc["subtasks"]) else None
    if next_item and next_item["role"]!=item["role"]:
        add_message(doc,item["role"],f"Đã bàn giao kết quả cho {ROLES[next_item['role']]}.","handoff",tool,item["artifact_id"],to_role=next_item["role"])
    return item


def stop_subtasks(doc, status, message):
    for item in doc.get("subtasks",[]):
        if item["status"]=="running":
            item.update(status=status,error=message,finished_at=timestamp())
        elif item["status"]=="waiting":
            item.update(status="blocked",error="Chờ xử lý bước trước.")

