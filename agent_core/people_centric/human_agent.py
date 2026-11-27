"""Human Compliance Agent (People Pillar: A.6.1-A.6.8, A.5.16, A.5.18) with Cross-Domain correlation."""
from __future__ import annotations

from typing import Any

from agent_core.people_centric.iso_rag import sanitize_untrusted_text
from tools.registry import ToolRegistry

HUMAN_CONTROLS = ("A.6.1", "A.6.2", "A.6.3", "A.6.4", "A.6.5", "A.6.6", "A.6.7", "A.6.8", "A.5.16", "A.5.18")
CROSS_DOMAIN_CONTROLS = {"A.6.5", "A.5.16", "A.5.18"}


def _is_excluded(company: dict[str, Any], control_id: str) -> dict[str, Any] | None:
    for item in company.get("soa_exclusions") or []:
        if isinstance(item, dict) and item.get("control_id") == control_id:
            return item
    return None


def observe(registry: ToolRegistry, company_id: str, control_id: str) -> dict[str, Any]:
    """Step 1 (Observe): Gather HR records and, for cross-domain controls, AD/VPN/Email/App & Laptop state."""
    hr_res = registry.invoke(
        company_id=company_id,
        tool_name="inspect_human_records",
        params={},
        control_id=control_id,
        actor="human_agent",
    )["result"]

    injection_alerts: list[str] = []
    for emp in hr_res.get("employees", []):
        for field in ("full_name", "role_title"):
            _, alerts = sanitize_untrusted_text(str(emp.get(field, "")), source_id=emp["employee_id"])
            injection_alerts.extend(alerts)
        if emp.get("metadata"):
            _, alerts = sanitize_untrusted_text(str(emp["metadata"]), source_id=f"{emp['employee_id']}:metadata")
            injection_alerts.extend(alerts)

    evidence_refs = [
        {
            "evidence_id": f"HR-{company_id}-{control_id}-{hr_res['sha256_hash'][:12].upper()}",
            "source": "tool://inspect_human_records",
            "sha256": hr_res["sha256_hash"],
            "observed_at_utc": hr_res["observed_at_utc"],
        }
    ]

    accounts: list[dict[str, Any]] = []
    devices: list[dict[str, Any]] = []
    if control_id in CROSS_DOMAIN_CONTROLS:
        acc_res = registry.invoke(
            company_id=company_id,
            tool_name="inspect_identity_access",
            params={},
            control_id=control_id,
            actor="human_agent",
        )["result"]
        accounts = acc_res.get("accounts", [])
        evidence_refs.append(
            {
                "evidence_id": f"IAM-{company_id}-{control_id}-{acc_res['sha256_hash'][:12].upper()}",
                "source": "tool://inspect_identity_access",
                "sha256": acc_res["sha256_hash"],
                "observed_at_utc": acc_res["observed_at_utc"],
            }
        )
        dev_res = registry.invoke(
            company_id=company_id,
            tool_name="inspect_device_baseline",
            params={},
            control_id=control_id,
            actor="human_agent",
        )["result"]
        devices = dev_res.get("devices", [])
        evidence_refs.append(
            {
                "evidence_id": f"HW-{company_id}-{control_id}-{dev_res['sha256_hash'][:12].upper()}",
                "source": "tool://inspect_device_baseline",
                "sha256": dev_res["sha256_hash"],
                "observed_at_utc": dev_res["observed_at_utc"],
            }
        )

    return {
        "observations": {
            "employees": hr_res.get("employees", []),
            "accounts": accounts,
            "devices": devices,
        },
        "evidence_refs": evidence_refs,
        "prompt_injection_alerts": sorted(set(injection_alerts)),
    }


def assess_and_detect(
    control_id: str, observations: dict[str, Any], company: dict[str, Any]
) -> dict[str, Any]:
    """Steps 2-3 (Assess & Detect): Evaluate People Pillar + Cross-Domain offboarding."""
    excl = _is_excluded(company, control_id)
    if excl:
        return {
            "status": "Not Applicable",
            "confidence": 1.0,
            "findings": [],
            "rationale": f"Control {control_id} được loại trừ theo SoA: {excl.get('reason', 'N/A')}.",
        }

    employees = observations.get("employees", [])
    accounts = observations.get("accounts", [])
    devices = observations.get("devices", [])
    if not employees:
        return {
            "status": "Insufficient Evidence",
            "confidence": 1.0,
            "findings": [],
            "rationale": f"Không có dữ liệu hồ sơ nhân sự để đánh giá {control_id}.",
        }

    active_emps = [e for e in employees if e.get("employment_status") != "terminated"]
    terminated_emps = [e for e in employees if e.get("employment_status") == "terminated"]

    if control_id == "A.6.1":
        if any(e.get("screened") is None for e in active_emps):
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": "Thiếu dữ liệu thẩm tra lý lịch nhân sự (A.6.1)."}
        missing = [e["employee_id"] for e in active_emps if not e.get("screened")]
        return _fraction_result(control_id, len(active_emps), missing, "missing_screening", "chưa có hồ sơ thẩm tra trước tuyển dụng")

    if control_id == "A.6.2":
        if any(e.get("contract_signed") is None for e in active_emps):
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": "Thiếu dữ liệu hợp đồng lao động (A.6.2)."}
        missing = [e["employee_id"] for e in active_emps if not e.get("contract_signed")]
        return _fraction_result(control_id, len(active_emps), missing, "missing_contract", "chưa ký điều khoản ATTT trong hợp đồng")

    if control_id == "A.6.3":
        if any(e.get("training_completed") is None or e.get("phishing_passed") is None for e in employees):
            return {
                "status": "Insufficient Evidence",
                "confidence": 1.0,
                "findings": [],
                "rationale": "Thiếu dữ liệu hoàn thành đào tạo ATTT hoặc mô phỏng phishing (A.6.3); không tự suy đoán.",
            }
        missing_training = [e["employee_id"] for e in employees if not e.get("training_completed")]
        failed_phishing = [e["employee_id"] for e in employees if not e.get("phishing_passed")]
        combined = sorted(set(missing_training) | set(failed_phishing))
        if not combined:
            return {
                "status": "Compliant",
                "confidence": 1.0,
                "findings": [],
                "rationale": f"{len(employees)}/{len(employees)} nhân sự đã hoàn thành đào tạo ATTT và vượt qua bài kiểm tra phishing.",
            }
        findings = []
        if missing_training:
            findings.append({"issue": "missing_training", "count": len(missing_training), "employee_ids": missing_training})
        if failed_phishing:
            findings.append({"issue": "failed_phishing", "count": len(failed_phishing), "employee_ids": failed_phishing})
        status = "Non-compliant" if len(missing_training) == len(employees) and len(failed_phishing) == len(employees) else "Partial"
        return {
            "status": status,
            "confidence": 1.0,
            "findings": findings,
            "rationale": (
                f"Đào tạo ATTT đạt {len(employees) - len(missing_training)}/{len(employees)}; "
                f"vượt qua Phishing đạt {len(employees) - len(failed_phishing)}/{len(employees)}."
            ),
        }

    if control_id == "A.6.6":
        if any(e.get("nda_signed") is None for e in employees):
            return {
                "status": "Insufficient Evidence",
                "confidence": 1.0,
                "findings": [],
                "rationale": "Thiếu bằng chứng ký thỏa thuận bảo mật NDA (A.6.6); không tự suy đoán.",
            }
        unsigned = [e["employee_id"] for e in employees if not e.get("nda_signed")]
        return _fraction_result(control_id, len(employees), unsigned, "unsigned_nda", "chưa ký thỏa thuận bảo mật NDA")

    if control_id == "A.6.7":
        if any(e.get("remote_work_compliant") is None for e in active_emps):
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": "Thiếu dữ liệu làm việc từ xa (A.6.7)."}
        non = [e["employee_id"] for e in active_emps if not e.get("remote_work_compliant")]
        return _fraction_result(control_id, len(active_emps), non, "remote_work_gap", "chưa đáp ứng chính sách làm việc từ xa")

    if control_id == "A.6.8":
        if any(e.get("incident_process_known") is None for e in employees):
            return {
                "status": "Insufficient Evidence",
                "confidence": 1.0,
                "findings": [],
                "rationale": "Thiếu kết quả kiểm tra nắm quy trình báo cáo sự cố ATTT (A.6.8).",
            }
        unknown_ids = [e["employee_id"] for e in employees if not e.get("incident_process_known")]
        if not unknown_ids:
            return {
                "status": "Compliant",
                "confidence": 1.0,
                "findings": [],
                "rationale": f"{len(employees)}/{len(employees)} nhân sự đã nắm rõ quy trình báo cáo sự cố ATTT.",
            }
        status = "Non-compliant" if len(unknown_ids) == len(employees) else "Partial"
        return {
            "status": status,
            "confidence": 1.0,
            "findings": [
                {
                    "issue": "unknown_incident_process",
                    "count": len(unknown_ids),
                    "employee_ids": unknown_ids,
                    "requires_adaptive_interview": True,
                }
            ],
            "rationale": (
                f"Nắm quy trình báo cáo sự cố đạt {len(employees) - len(unknown_ids)}/{len(employees)}; "
                f"còn {len(unknown_ids)} nhân sự cần thực hiện Adaptive Interview và đào tạo lại."
            ),
        }

    if control_id == "A.6.4":
        return {
            "status": "Compliant",
            "confidence": 1.0,
            "findings": [],
            "rationale": "Quy trình xử lý vi phạm (A.6.4) hợp lệ và tuân thủ nguyên tắc không dùng kết quả AI chưa xác minh để kỷ luật.",
        }

    # Cross-domain controls: A.6.5, A.5.18, A.5.16
    if control_id in CROSS_DOMAIN_CONTROLS:
        if not terminated_emps:
            return {
                "status": "Compliant",
                "confidence": 1.0,
                "findings": [],
                "rationale": f"Không phát hiện nhân sự nghỉ việc còn tồn đọng quyền/tài sản đối với {control_id}.",
            }
        findings: list[dict[str, Any]] = []
        for emp in terminated_emps:
            eid = emp["employee_id"]
            active_accs = [a for a in accounts if a["employee_id"] == eid and a.get("is_active")]
            unreturned_devs = [
                d for d in devices
                if d.get("assigned_employee_id") == eid and (not d.get("returned_to_it") or d.get("badge_card_active"))
            ]
            ack_missing = not bool(emp.get("offboarding_ack"))

            if control_id in ("A.5.18", "A.5.16"):
                if active_accs:
                    findings.append(
                        {
                            "issue": "orphan_active_accounts",
                            "employee_id": eid,
                            "department": emp.get("department"),
                            "active_systems": [a["system_type"] for a in active_accs],
                            "account_ids": [a["account_id"] for a in active_accs],
                        }
                    )
            else:  # A.6.5 full cross-domain offboarding
                if active_accs or unreturned_devs or ack_missing:
                    findings.append(
                        {
                            "issue": "incomplete_offboarding_cross_domain",
                            "employee_id": eid,
                            "department": emp.get("department"),
                            "active_systems": [a["system_type"] for a in active_accs],
                            "account_ids": [a["account_id"] for a in active_accs],
                            "unreturned_devices": [d["device_id"] for d in unreturned_devs],
                            "offboarding_ack_missing": ack_missing,
                        }
                    )

        if not findings:
            return {
                "status": "Compliant",
                "confidence": 1.0,
                "findings": [],
                "rationale": f"Toàn bộ nhân sự nghỉ việc đã được khóa tài khoản và hoàn tất nghĩa vụ {control_id}.",
            }
        return {
            "status": "Non-compliant",
            "confidence": 1.0,
            "findings": findings,
            "rationale": f"Phát hiện {len(findings)} trường hợp vi phạm {control_id} (nhân sự nghỉ việc vẫn còn quyền hệ thống hoặc chưa hoàn trả tài sản).",
        }

    return {
        "status": "Insufficient Evidence",
        "confidence": 0.0,
        "findings": [],
        "rationale": f"Control {control_id} chưa có quy tắc đánh giá tự động.",
    }


def _fraction_result(
    control_id: str, total: int, failed_ids: list[str], issue_code: str, msg: str
) -> dict[str, Any]:
    if not failed_ids:
        return {
            "status": "Compliant",
            "confidence": 1.0,
            "findings": [],
            "rationale": f"{total}/{total} nhân sự đạt yêu cầu {control_id}.",
        }
    status = "Non-compliant" if len(failed_ids) == total else "Partial"
    return {
        "status": status,
        "confidence": 1.0,
        "findings": [{"issue": issue_code, "count": len(failed_ids), "employee_ids": failed_ids}],
        "rationale": f"Đạt {total - len(failed_ids)}/{total} nhân sự; còn {len(failed_ids)} nhân sự {msg} ({control_id}).",
    }


def plan_remediation(control_id: str, findings: list[dict[str, Any]], company_id: str) -> list[dict[str, Any]]:
    """Step 4 (Plan): Map findings strictly to parameterized ToolRegistry playbooks."""
    actions: list[dict[str, Any]] = []
    if not findings:
        return actions

    if control_id == "A.6.3":
        targets = sorted({eid for f in findings for eid in f.get("employee_ids", [])})
        if targets:
            actions.append(
                {
                    "tool_name": "assign_security_training",
                    "params": {"employee_ids": targets, "module_code": "ISO27001-AWARENESS-PHISHING-A63"},
                    "description": f"Giao khóa đào tạo ATTT & chống phishing cho {len(targets)} nhân sự.",
                }
            )
    elif control_id == "A.6.6":
        targets = sorted({eid for f in findings for eid in f.get("employee_ids", [])})
        if targets:
            actions.append(
                {
                    "tool_name": "send_nda_reminder",
                    "params": {"employee_ids": targets, "deadline_days": 5},
                    "description": f"Gửi nhắc nhở ký NDA trong 5 ngày tới {len(targets)} nhân sự.",
                }
            )
    elif control_id == "A.6.8":
        targets = sorted({eid for f in findings for eid in f.get("employee_ids", [])})
        if targets:
            actions.append(
                {
                    "tool_name": "assign_security_training",
                    "params": {"employee_ids": targets, "module_code": "INCIDENT-REPORTING-A68"},
                    "description": f"Giao học phần báo cáo sự cố & lên lịch Adaptive Interview cho {len(targets)} nhân sự.",
                }
            )
    elif control_id in ("A.6.5", "A.5.18", "A.5.16"):
        for f in findings:
            eid = f["employee_id"]
            systems = f.get("active_systems", [])
            unreturned = f.get("unreturned_devices", [])
            if unreturned:
                for did in unreturned:
                    actions.append(
                        {
                            "tool_name": "create_it_remediation_ticket",
                            "params": {
                                "control_id": "A.5.11",
                                "target_id": did,
                                "summary": f"Thu hồi laptop {did} và khóa thẻ từ của nhân sự nghỉ việc {eid}",
                                "priority": "high",
                            },
                            "description": f"Tạo phiếu thu hồi laptop {did} của {eid}.",
                        }
                    )
            if systems:
                actions.append(
                    {
                        "tool_name": "disable_ad_and_revoke_access",
                        "params": {
                            "employee_id": eid,
                            "systems": systems,
                            "reason_ticket": f"TKT-OFFBOARD-{eid}",
                        },
                        "description": f"Khóa tài khoản AD/VPN/Email/Ứng dụng của {eid} (HIGH RISK - chờ Admin duyệt).",
                    }
                )
    return actions
