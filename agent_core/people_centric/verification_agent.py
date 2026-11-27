"""Verification Agent: mandatory fresh evidence re-inspection before moving to Compliant."""
from __future__ import annotations

from typing import Any

from agent_core.people_centric import hardware_agent, human_agent, software_agent
from backend.pc_storage import BasePCStore, utc_now_iso
from tools.registry import ToolRegistry

NON_TECHNICAL_HOLDING_TOOLS = {
    "send_nda_reminder",
    "assign_security_training",
    "create_it_remediation_ticket",
}


def _agent_module_for_control(control_id: str):
    if control_id in human_agent.HUMAN_CONTROLS:
        return human_agent
    if control_id in hardware_agent.HARDWARE_CONTROLS:
        return hardware_agent
    if control_id in software_agent.SOFTWARE_CONTROLS:
        return software_agent
    return human_agent


def verify_control(
    *,
    store: BasePCStore,
    registry: ToolRegistry,
    company_id: str,
    control_id: str,
    executed_actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Re-collect live/fresh observations and verify against ISO baseline before approving Compliant."""
    company = store.get_company(company_id)
    if not company:
        raise KeyError(f"Company not found: {company_id}")

    agent_mod = _agent_module_for_control(control_id)
    fresh_obs = agent_mod.observe(registry, company_id, control_id)
    reassessed = agent_mod.assess_and_detect(control_id, fresh_obs["observations"], company)

    actions = executed_actions or []
    has_pending_approval = any(a.get("status") == "PENDING_APPROVAL" for a in actions)
    has_human_followup_only = any(a.get("tool_name") in NON_TECHNICAL_HOLDING_TOOLS for a in actions)

    # Strict Verifiable rule: NEVER claim Compliant while evidence still shows gaps or awaits human execution
    if reassessed["status"] == "Compliant" and not has_pending_approval:
        verified_at = utc_now_iso()
        for act in actions:
            aid = act.get("action_id")
            if aid:
                rec = store.get_remediation_action(company_id, aid)
                if rec and rec["approval_status"] in ("EXECUTED", "AUTO_APPROVED"):
                    store.save_remediation_action(
                        {
                            **rec,
                            "approval_status": "VERIFIED",
                            "verification_data": {
                                "verified_at_utc": verified_at,
                                "control_status": "Compliant",
                                "fresh_evidence_refs": fresh_obs["evidence_refs"],
                            },
                        }
                    )
        return {
            "verification_passed": True,
            "final_status": "Compliant",
            "needs_retry": False,
            "findings": [],
            "fresh_evidence_refs": fresh_obs["evidence_refs"],
            "verification_summary": f"Xác minh lại thành công lúc {verified_at}: {reassessed['rationale']}",
        }

    if has_pending_approval or has_human_followup_only:
        return {
            "verification_passed": False,
            "final_status": "Pending Remediation",
            "needs_retry": False,
            "findings": reassessed["findings"],
            "fresh_evidence_refs": fresh_obs["evidence_refs"],
            "verification_summary": (
                "Đang giữ trạng thái Pending Remediation: đã gửi nhắc nhở/đào tạo/ticket hoặc đang chờ "
                "Quản trị viên phê duyệt và có bằng chứng hoàn tất thực tế."
            ),
        }

    return {
        "verification_passed": False,
        "final_status": reassessed["status"],
        "needs_retry": True,
        "findings": reassessed["findings"],
        "fresh_evidence_refs": fresh_obs["evidence_refs"],
        "verification_summary": f"Xác minh lại chưa đạt ({reassessed['status']}): {reassessed['rationale']}",
    }
