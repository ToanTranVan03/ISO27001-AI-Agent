"""Hardware Compliance Agent (A.5.9, A.5.11, A.7.7, A.7.9, A.7.10, A.7.14, A.8.1, A.8.24)."""
from __future__ import annotations

from typing import Any

from tools.registry import ToolRegistry

HARDWARE_CONTROLS = ("A.5.9", "A.5.11", "A.7.7", "A.7.9", "A.7.10", "A.7.14", "A.8.1", "A.8.24")


def _is_excluded(company: dict[str, Any], control_id: str) -> dict[str, Any] | None:
    for item in company.get("soa_exclusions") or []:
        if isinstance(item, dict) and item.get("control_id") == control_id:
            return item
    return None


def observe(registry: ToolRegistry, company_id: str, control_id: str) -> dict[str, Any]:
    dev_res = registry.invoke(
        company_id=company_id,
        tool_name="inspect_device_baseline",
        params={},
        control_id=control_id,
        actor="hardware_agent",
    )["result"]
    hr_res = registry.invoke(
        company_id=company_id,
        tool_name="inspect_human_records",
        params={},
        control_id=control_id,
        actor="hardware_agent",
    )["result"]

    return {
        "observations": {
            "devices": dev_res.get("devices", []),
            "baseline_policy": dev_res.get("baseline_policy", {}),
            "employees": hr_res.get("employees", []),
        },
        "evidence_refs": [
            {
                "evidence_id": f"HW-{company_id}-{control_id}-{dev_res['sha256_hash'][:12].upper()}",
                "source": "tool://inspect_device_baseline",
                "sha256": dev_res["sha256_hash"],
                "observed_at_utc": dev_res["observed_at_utc"],
            },
            {
                "evidence_id": f"HR-{company_id}-{control_id}-{hr_res['sha256_hash'][:12].upper()}",
                "source": "tool://inspect_human_records",
                "sha256": hr_res["sha256_hash"],
                "observed_at_utc": hr_res["observed_at_utc"],
            },
        ],
        "prompt_injection_alerts": [],
    }


def assess_and_detect(
    control_id: str, observations: dict[str, Any], company: dict[str, Any]
) -> dict[str, Any]:
    excl = _is_excluded(company, control_id)
    if excl:
        return {
            "status": "Not Applicable",
            "confidence": 1.0,
            "findings": [],
            "rationale": f"Control {control_id} được loại trừ theo SoA: {excl.get('reason', 'N/A')}.",
        }

    devices = observations.get("devices", [])
    employees = {e["employee_id"]: e for e in observations.get("employees", [])}
    policy = observations.get("baseline_policy") or company.get("baseline_policy") or {}
    max_lock = int(policy.get("screen_lock_minutes_max", 5))

    if not devices:
        return {
            "status": "Insufficient Evidence",
            "confidence": 1.0,
            "findings": [],
            "rationale": f"Không có dữ liệu thiết bị đầu cuối để đánh giá {control_id}.",
        }

    if control_id == "A.5.11":
        terminated_ids = {eid for eid, e in employees.items() if e.get("employment_status") == "terminated"}
        findings = [
            {
                "issue": "unreturned_hardware_or_active_badge",
                "device_id": d["device_id"],
                "employee_id": d.get("assigned_employee_id"),
                "returned_to_it": d.get("returned_to_it"),
                "badge_card_active": d.get("badge_card_active"),
            }
            for d in devices
            if d.get("assigned_employee_id") in terminated_ids and (not d.get("returned_to_it") or d.get("badge_card_active"))
        ]
        if not findings:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": "Toàn bộ thiết bị và thẻ từ của nhân sự nghỉ việc đã được thu hồi (A.5.11)."}
        return {
            "status": "Non-compliant",
            "confidence": 1.0,
            "findings": findings,
            "rationale": f"Phát hiện {len(findings)} thiết bị/thẻ từ thuộc nhân sự nghỉ việc chưa hoàn trả IT (A.5.11).",
        }

    if control_id == "A.5.9":
        orphans = [d["device_id"] for d in devices if not d.get("assigned_employee_id") or d.get("assigned_employee_id") not in employees]
        if not orphans:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": f"{len(devices)}/{len(devices)} thiết bị đều có chủ sở hữu hợp lệ (A.5.9)."}
        return {"status": "Partial", "confidence": 1.0, "findings": [{"issue": "orphan_device", "device_ids": orphans}], "rationale": f"Còn {len(orphans)} thiết bị chưa gắn chủ sở hữu hợp lệ."}

    if control_id == "A.7.7":
        if any(d.get("screen_lock_minutes") is None for d in devices):
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": "Thiếu thông số thời gian khóa màn hình trên thiết bị (A.7.7)."}
        bad = [d["device_id"] for d in devices if int(d["screen_lock_minutes"]) > max_lock]
        return _dev_fraction(control_id, len(devices), bad, "screen_lock_too_long", f"cấu hình khóa màn hình vượt quá {max_lock} phút")

    if control_id in ("A.8.24", "A.7.9"):
        if any(d.get("disk_encrypted") is None for d in devices):
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": f"Thiếu trạng thái mã hóa ổ đĩa BitLocker/LUKS ({control_id})."}
        bad = [d["device_id"] for d in devices if not d.get("disk_encrypted")]
        return _dev_fraction(control_id, len(devices), bad, "disk_unencrypted", "chưa bật mã hóa ổ đĩa")

    if control_id == "A.7.10":
        bad = [d["device_id"] for d in devices if int(d.get("usb_unauthorized_events", 0)) > 0]
        if not bad:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": "Không phát hiện sự kiện cắm USB trái phép (A.7.10)."}
        return {"status": "Non-compliant", "confidence": 1.0, "findings": [{"issue": "unauthorized_usb", "device_ids": bad}], "rationale": f"Phát hiện hành vi cắm USB trái phép trên {len(bad)} thiết bị."}

    if control_id == "A.7.14":
        terminated_ids = {eid for eid, e in employees.items() if e.get("employment_status") == "terminated"}
        returned_unverified = [
            d["device_id"] for d in devices
            if d.get("assigned_employee_id") in terminated_ids and d.get("returned_to_it") and not d.get("disposal_verified")
        ]
        if not returned_unverified:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": "Không tồn đọng thiết bị chờ xác nhận xóa dữ liệu thanh lý (A.7.14)."}
        return {"status": "Partial", "confidence": 1.0, "findings": [{"issue": "unverified_wipe", "device_ids": returned_unverified}], "rationale": f"Còn {len(returned_unverified)} thiết bị đã thu hồi chưa xác nhận xóa sạch dữ liệu."}

    if control_id == "A.8.1":
        if any(d.get("firewall_enabled") is None or d.get("screen_lock_minutes") is None or d.get("disk_encrypted") is None for d in devices):
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": "Thiếu dữ liệu cấu hình thiết bị đầu cuối (A.8.1)."}
        bad = [
            d["device_id"] for d in devices
            if not d.get("firewall_enabled") or int(d["screen_lock_minutes"]) > max_lock or not d.get("disk_encrypted")
        ]
        return _dev_fraction(control_id, len(devices), bad, "endpoint_hardening_gap", "chưa đạt đủ cấu hình bảo vệ đầu cuối")

    return {"status": "Insufficient Evidence", "confidence": 0.0, "findings": [], "rationale": f"Control {control_id} chưa có rule phần cứng."}


def _dev_fraction(control_id: str, total: int, bad_ids: list[str], issue: str, msg: str) -> dict[str, Any]:
    if not bad_ids:
        return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": f"{total}/{total} thiết bị đạt tiêu chuẩn {control_id}."}
    status = "Non-compliant" if len(bad_ids) == total else "Partial"
    return {
        "status": status,
        "confidence": 1.0,
        "findings": [{"issue": issue, "device_ids": bad_ids, "count": len(bad_ids)}],
        "rationale": f"{total - len(bad_ids)}/{total} thiết bị đạt; {len(bad_ids)} thiết bị {msg} ({control_id}).",
    }


def plan_remediation(control_id: str, findings: list[dict[str, Any]], company_id: str) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not findings:
        return actions
    if control_id == "A.5.11":
        for f in findings:
            actions.append(
                {
                    "tool_name": "create_it_remediation_ticket",
                    "params": {
                        "control_id": "A.5.11",
                        "target_id": f["device_id"],
                        "summary": f"Thu hồi laptop {f['device_id']} và vô hiệu hóa thẻ từ của {f.get('employee_id')}",
                        "priority": "high",
                    },
                    "description": f"Phiếu thu hồi thiết bị {f['device_id']}.",
                }
            )
    elif control_id in ("A.7.7", "A.8.1"):
        for did in sorted({d for f in findings for d in f.get("device_ids", [])}):
            actions.append(
                {
                    "tool_name": "sync_device_baseline_gpo",
                    "params": {"device_id": did, "baseline_profile_id": "ISO27001-BASELINE-V1"},
                    "description": f"Đồng bộ GPO khóa màn hình & hardening đầu cuối cho {did}.",
                }
            )
    elif control_id in ("A.8.24", "A.7.9"):
        for did in sorted({d for f in findings for d in f.get("device_ids", [])}):
            actions.append(
                {
                    "tool_name": "enforce_disk_encryption",
                    "params": {"device_id": did, "recovery_key_vault_ref": f"VAULT-{company_id}-{did}"},
                    "description": f"Bật mã hóa ổ đĩa BitLocker/LUKS cho {did} (HIGH RISK - chờ Admin duyệt).",
                }
            )
    else:
        for did in sorted({d for f in findings for d in f.get("device_ids", [])}):
            actions.append(
                {
                    "tool_name": "create_it_remediation_ticket",
                    "params": {
                        "control_id": control_id,
                        "target_id": did,
                        "summary": f"Xử lý sai lệch phần cứng {control_id} trên {did}",
                        "priority": "medium",
                    },
                    "description": f"Tạo ticket xử lý {control_id} trên {did}.",
                }
            )
    return actions
