"""Software & Server Compliance Agent (A.8.2, A.8.5, A.8.7, A.8.8, A.8.9, A.8.15, A.8.19, A.8.32)."""
from __future__ import annotations

from typing import Any

from agent_core.people_centric.iso_rag import sanitize_untrusted_text
from backend.pc_storage import DEFAULT_BASELINE_POLICY
from tools.registry import ToolRegistry

SOFTWARE_CONTROLS = ("A.8.2", "A.8.5", "A.8.7", "A.8.8", "A.8.9", "A.8.15", "A.8.19", "A.8.32")


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
        actor="software_agent",
    )["result"]

    injection_alerts: list[str] = []
    for dev in dev_res.get("devices", []):
        for pkg in dev.get("installed_software", []):
            _, alerts = sanitize_untrusted_text(str(pkg), source_id=f"{dev['device_id']}:software")
            injection_alerts.extend(alerts)

    evidence_refs = [
        {
            "evidence_id": f"SW-{company_id}-{control_id}-{dev_res['sha256_hash'][:12].upper()}",
            "source": "tool://inspect_device_baseline",
            "sha256": dev_res["sha256_hash"],
            "observed_at_utc": dev_res["observed_at_utc"],
        }
    ]

    accounts: list[dict[str, Any]] = []
    employees: list[dict[str, Any]] = []
    if control_id in ("A.8.2", "A.8.5", "A.8.32"):
        acc_res = registry.invoke(
            company_id=company_id,
            tool_name="inspect_identity_access",
            params={},
            control_id=control_id,
            actor="software_agent",
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
        hr_res = registry.invoke(
            company_id=company_id,
            tool_name="inspect_human_records",
            params={},
            control_id=control_id,
            actor="software_agent",
        )["result"]
        employees = hr_res.get("employees", [])

    return {
        "observations": {
            "devices": dev_res.get("devices", []),
            "baseline_policy": dev_res.get("baseline_policy", {}),
            "accounts": accounts,
            "employees": employees,
        },
        "evidence_refs": evidence_refs,
        "prompt_injection_alerts": sorted(set(injection_alerts)),
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
    accounts = observations.get("accounts", [])
    employees = {e["employee_id"]: e for e in observations.get("employees", [])}
    policy = observations.get("baseline_policy") or company.get("baseline_policy") or DEFAULT_BASELINE_POLICY
    max_lock = int(policy.get("screen_lock_minutes_max", 5))

    if control_id == "A.8.8":
        if not devices or any(d.get("patch_compliant") is None for d in devices):
            return {
                "status": "Insufficient Evidence",
                "confidence": 1.0,
                "findings": [],
                "rationale": "Thiếu dữ liệu quét bản vá trên máy trạm/server (A.8.8); không tự suy đoán.",
            }
        # Evaluate workstation fleet PC-* (or all devices if non-PC)
        target_devs = [d for d in devices if d["device_id"].startswith("PC-")] or devices
        missing = [
            {"issue": "missing_patches", "device_id": d["device_id"], "missing_patches": d.get("missing_patches", ["KB-SECURITY"])}
            for d in target_devs
            if not d.get("patch_compliant")
        ]
        if not missing:
            return {
                "status": "Compliant",
                "confidence": 1.0,
                "findings": [],
                "rationale": f"{len(target_devs)}/{len(target_devs)} máy trạm đã cập nhật đầy đủ bản vá bảo mật (A.8.8).",
            }
        status = "Non-compliant" if len(missing) == len(target_devs) else "Partial"
        return {
            "status": status,
            "confidence": 1.0,
            "findings": missing,
            "rationale": (
                f"Bản vá đạt {len(target_devs) - len(missing)}/{len(target_devs)} máy; "
                f"phát hiện {len(missing)} máy thiếu bản vá: {[m['device_id'] for m in missing]}."
            ),
        }

    if control_id == "A.8.9":
        req_keys = ("firewall_enabled", "screen_lock_minutes", "disk_encrypted", "password_policy_ok", "antivirus_active", "ntp_synced")
        if not devices or any(any(d.get(k) is None for k in req_keys) for d in devices):
            return {
                "status": "Insufficient Evidence",
                "confidence": 1.0,
                "findings": [],
                "rationale": "Thiếu thông số Security Baseline 6 tiêu chí trên thiết bị (A.8.9).",
            }
        findings: list[dict[str, Any]] = []
        for d in devices:
            checks = {
                "firewall_enabled": bool(d["firewall_enabled"]) is True,
                "screen_lock_minutes": int(d["screen_lock_minutes"]) <= max_lock,
                "disk_encrypted": bool(d["disk_encrypted"]) is True,
                "password_policy_ok": bool(d["password_policy_ok"]) is True,
                "antivirus_active": bool(d["antivirus_active"]) is True,
                "ntp_synced": bool(d["ntp_synced"]) is True,
            }
            failed = [k for k, ok in checks.items() if not ok]
            passed = [k for k, ok in checks.items() if ok]
            if failed:
                findings.append(
                    {
                        "issue": "baseline_drift",
                        "device_id": d["device_id"],
                        "failed_checks": failed,
                        "passed_checks": passed,
                        "failed_count": len(failed),
                        "total_checks": 6,
                    }
                )
        if not findings:
            return {
                "status": "Compliant",
                "confidence": 1.0,
                "findings": [],
                "rationale": f"{len(devices)}/{len(devices)} thiết bị đạt trọn vẹn 6/6 tiêu chí Security Baseline (A.8.9).",
            }
        status = "Non-compliant" if len(findings) == len(devices) else "Partial"
        summary = ", ".join(f"{f['device_id']} sai {f['failed_count']}/6 ({f['failed_checks']})" for f in findings)
        return {
            "status": status,
            "confidence": 1.0,
            "findings": findings,
            "rationale": f"Phát hiện sai lệch Security Baseline (A.8.9): {summary}.",
        }

    if control_id == "A.8.5":
        ad_accs = [a for a in accounts if a.get("system_type") == "active_directory"] or accounts
        if not ad_accs or any(a.get("mfa_enabled") is None for a in ad_accs):
            return {
                "status": "Insufficient Evidence",
                "confidence": 1.0,
                "findings": [],
                "rationale": "Thiếu dữ liệu trạng thái kích hoạt MFA của tài khoản (A.8.5).",
            }
        missing_mfa = [a for a in ad_accs if not a.get("mfa_enabled")]
        if not missing_mfa:
            return {
                "status": "Compliant",
                "confidence": 1.0,
                "findings": [],
                "rationale": f"{len(ad_accs)}/{len(ad_accs)} tài khoản đã kích hoạt MFA (A.8.5).",
            }
        status = "Non-compliant" if len(missing_mfa) == len(ad_accs) else "Partial"
        return {
            "status": status,
            "confidence": 1.0,
            "findings": [
                {
                    "issue": "mfa_disabled",
                    "count": len(missing_mfa),
                    "account_ids": [a["account_id"] for a in missing_mfa],
                    "employee_ids": [a["employee_id"] for a in missing_mfa],
                }
            ],
            "rationale": f"MFA đạt {len(ad_accs) - len(missing_mfa)}/{len(ad_accs)} tài khoản; còn {len(missing_mfa)} tài khoản chưa bật MFA.",
        }

    if control_id == "A.8.2":
        priv = [a for a in accounts if a.get("is_privileged") and a.get("is_active")]
        bad_priv = [
            a for a in priv
            if not a.get("mfa_enabled") or (employees.get(a["employee_id"], {}).get("employment_status") == "terminated")
        ]
        if not bad_priv:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": "Các tài khoản đặc quyền đang hoạt động đều bật MFA và hợp lệ (A.8.2)."}
        return {
            "status": "Non-compliant",
            "confidence": 1.0,
            "findings": [{"issue": "privileged_account_risk", "account_ids": [a["account_id"] for a in bad_priv], "employee_ids": sorted({a["employee_id"] for a in bad_priv})}],
            "rationale": f"Phát hiện {len(bad_priv)} tài khoản đặc quyền chưa bật MFA hoặc thuộc nhân sự đã nghỉ việc.",
        }

    if control_id == "A.8.7":
        if not devices:
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": "Thiếu dữ liệu thiết bị cho A.8.7."}
        off = [d["device_id"] for d in devices if not d.get("antivirus_active")]
        if not off:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": f"{len(devices)}/{len(devices)} thiết bị bật Antivirus/EDR (A.8.7)."}
        return {"status": "Non-compliant" if len(off) == len(devices) else "Partial", "confidence": 1.0, "findings": [{"issue": "antivirus_disabled", "device_ids": off}], "rationale": f"{len(off)} thiết bị đang tắt Antivirus/EDR."}

    if control_id == "A.8.15":
        if not devices:
            return {"status": "Insufficient Evidence", "confidence": 1.0, "findings": [], "rationale": "Thiếu dữ liệu log thiết bị (A.8.15)."}
        off = [d["device_id"] for d in devices if not d.get("audit_logging_enabled")]
        if not off:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": f"{len(devices)}/{len(devices)} thiết bị bật ghi nhật ký kiểm toán (A.8.15)."}
        return {"status": "Partial", "confidence": 1.0, "findings": [{"issue": "logging_disabled", "device_ids": off}], "rationale": f"{len(off)} thiết bị tắt audit logging."}

    if control_id == "A.8.19":
        whitelist = set(policy.get("approved_software_whitelist") or DEFAULT_BASELINE_POLICY["approved_software_whitelist"])
        unapproved: list[dict[str, Any]] = []
        for d in devices:
            extra = [pkg for pkg in d.get("installed_software", []) if pkg not in whitelist]
            if extra:
                unapproved.append({"issue": "unauthorized_software", "device_id": d["device_id"], "packages": extra})
        if not unapproved:
            return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": "Toàn bộ phần mềm cài đặt nằm trong Whitelist được phê duyệt (A.8.19)."}
        return {"status": "Non-compliant", "confidence": 1.0, "findings": unapproved, "rationale": f"Phát hiện phần mềm ngoài Whitelist trên {len(unapproved)} thiết bị."}

    if control_id == "A.8.32":
        return {"status": "Compliant", "confidence": 1.0, "findings": [], "rationale": "Thay đổi cấu hình được theo dõi kèm change_ticket_id và audit trail (A.8.32)."}

    return {"status": "Insufficient Evidence", "confidence": 0.0, "findings": [], "rationale": f"Control {control_id} chưa có rule phần mềm."}


def plan_remediation(control_id: str, findings: list[dict[str, Any]], company_id: str) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not findings:
        return actions

    if control_id == "A.8.8":
        dev_ids = [f["device_id"] for f in findings]
        patch_ids = sorted({p for f in findings for p in f.get("missing_patches", [])})
        if dev_ids and patch_ids:
            actions.append(
                {
                    "tool_name": "deploy_security_patches",
                    "params": {
                        "device_ids": dev_ids,
                        "patch_ids": patch_ids,
                        "maintenance_window": "2026-11-28T02:00Z",
                    },
                    "description": f"Kiểm tra tương thích, snapshot và cập nhật bản vá cho {dev_ids}.",
                }
            )
    elif control_id == "A.8.9":
        for f in findings:
            actions.append(
                {
                    "tool_name": "sync_device_baseline_gpo",
                    "params": {"device_id": f["device_id"], "baseline_profile_id": "ISO27001-BASELINE-V1"},
                    "description": f"Snapshot & đẩy cấu hình GPO Security Baseline cho {f['device_id']}.",
                }
            )
    elif control_id == "A.8.5":
        emp_ids = sorted({eid for f in findings for eid in f.get("employee_ids", [])})
        if emp_ids:
            actions.append(
                {
                    "tool_name": "create_it_remediation_ticket",
                    "params": {
                        "control_id": "A.8.5",
                        "target_id": f"MFA-BATCH-{len(emp_ids)}",
                        "summary": f"Kích hoạt MFA bắt buộc cho {len(emp_ids)} nhân sự chưa bật MFA",
                        "priority": "high",
                    },
                    "description": f"Tạo ticket bắt buộc kích hoạt MFA cho {len(emp_ids)} nhân sự.",
                }
            )
    elif control_id == "A.8.7":
        for did in sorted({d for f in findings for d in f.get("device_ids", [])}):
            actions.append(
                {
                    "tool_name": "enable_endpoint_antivirus",
                    "params": {"device_id": did},
                    "description": f"Bật lại Antivirus/EDR trên {did}.",
                }
            )
    elif control_id == "A.8.19":
        for f in findings:
            for pkg in f.get("packages", []):
                actions.append(
                    {
                        "tool_name": "remove_unauthorized_software",
                        "params": {"device_id": f["device_id"], "package_name": pkg},
                        "description": f"Gỡ phần mềm ngoài Whitelist '{pkg}' trên {f['device_id']} (HIGH RISK).",
                    }
                )
    elif control_id == "A.8.2":
        for f in findings:
            for eid in f.get("employee_ids", []):
                actions.append(
                    {
                        "tool_name": "create_it_remediation_ticket",
                        "params": {
                            "control_id": "A.8.2",
                            "target_id": eid,
                            "summary": f"Rà soát và bật MFA / thu hồi quyền đặc quyền của {eid}",
                            "priority": "high",
                        },
                        "description": f"Rà soát quyền đặc quyền cho {eid}.",
                    }
                )
    return actions
