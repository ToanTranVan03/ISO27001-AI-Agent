"""3-Tier Risk-Gated Tool Registry with Dry-Run, RBAC company_id isolation, Snapshot/Rollback & Audit Log."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal
from uuid import uuid4

from pydantic import BaseModel

from backend.pc_storage import BasePCStore, sha256_json, utc_now_iso
from lab_adapters.base import ExecutionAdapter

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class ToolSecurityError(PermissionError):
    """Raised when an unknown/raw tool is invoked or tenant authorization fails."""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    risk_level: RiskLevel
    param_schema: type[BaseModel]
    description: str
    handler: Callable[[ExecutionAdapter, str, BaseModel, bool], dict[str, Any]]
    snapshot_fn: Callable[[ExecutionAdapter, str, BaseModel], dict[str, Any]] | None = None
    compatibility_fn: Callable[[ExecutionAdapter, str, BaseModel], dict[str, Any]] | None = None


class ToolRegistry:
    """Central security gateway for all AI Agent tool invocations."""

    def __init__(self, store: BasePCStore, adapter: ExecutionAdapter) -> None:
        self.store = store
        self.adapter = adapter
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        self._tools[definition.name] = definition

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "risk_level": t.risk_level,
                "description": t.description,
                "schema": t.param_schema.model_json_schema(),
            }
            for t in self._tools.values()
        ]

    def _audit(
        self,
        *,
        company_id: str,
        action_id: str | None,
        actor: str,
        tool_name: str,
        risk_level: str,
        dry_run: bool,
        params: dict[str, Any],
        result: dict[str, Any],
        status: str,
    ) -> None:
        self.store.append_audit_log(
            {
                "company_id": company_id,
                "action_id": action_id,
                "actor": actor,
                "tool_name": tool_name,
                "risk_level": risk_level,
                "dry_run": dry_run,
                "params_sha256": sha256_json(params),
                "result_sha256": sha256_json(result),
                "status": status,
            }
        )

    def invoke(
        self,
        *,
        company_id: str,
        tool_name: str,
        params: dict[str, Any],
        actor: str = "supervisor_agent",
        control_id: str = "GENERAL",
        assessment_run_id: str | None = None,
        dry_run: bool = False,
        allowed_companies: set[str] | None = None,
        require_medium_approval: bool = False,
    ) -> dict[str, Any]:
        # 1. Strict allowlist check (no raw PowerShell/Bash allowed)
        if tool_name not in self._tools:
            self._audit(
                company_id=company_id,
                action_id=None,
                actor=actor,
                tool_name=tool_name,
                risk_level="HIGH",
                dry_run=dry_run,
                params=params,
                result={"blocked": "unregistered_tool"},
                status="BLOCKED_SECURITY",
            )
            raise ToolSecurityError(f"Tool '{tool_name}' is not registered in Parameterized ToolRegistry.")

        # 2. Multi-tenant RBAC boundary check
        if allowed_companies is not None and company_id not in allowed_companies:
            self._audit(
                company_id=company_id,
                action_id=None,
                actor=actor,
                tool_name=tool_name,
                risk_level=self._tools[tool_name].risk_level,
                dry_run=dry_run,
                params=params,
                result={"blocked": "tenant_rbac_violation"},
                status="BLOCKED_RBAC",
            )
            raise ToolSecurityError(f"Actor '{actor}' is not authorized for company_id '{company_id}'.")

        if not self.store.get_company(company_id):
            raise ToolSecurityError(f"Unknown company_id '{company_id}'.")

        tool = self._tools[tool_name]
        validated = tool.param_schema.model_validate(params)
        clean_params = validated.model_dump(mode="json")

        # 3. Dry-run preview mode
        if dry_run:
            preview = tool.handler(self.adapter, company_id, validated, True)
            self._audit(
                company_id=company_id,
                action_id=None,
                actor=actor,
                tool_name=tool.name,
                risk_level=tool.risk_level,
                dry_run=True,
                params=clean_params,
                result=preview,
                status="DRY_RUN_PREVIEW",
            )
            return {
                "status": "DRY_RUN_PREVIEW",
                "tool_name": tool.name,
                "risk_level": tool.risk_level,
                "preview": preview,
            }

        # 4. HIGH RISK -> Mandatory Human-in-the-loop (NEVER execute directly from agent)
        if tool.risk_level == "HIGH":
            preview = tool.handler(self.adapter, company_id, validated, True)
            snapshot = tool.snapshot_fn(self.adapter, company_id, validated) if tool.snapshot_fn else None
            action_id = str(uuid4())
            action = self.store.save_remediation_action(
                {
                    "action_id": action_id,
                    "company_id": company_id,
                    "assessment_run_id": assessment_run_id,
                    "control_id": control_id,
                    "tool_name": tool.name,
                    "tool_params": clean_params,
                    "risk_level": "HIGH",
                    "approval_status": "PENDING_APPROVAL",
                    "dry_run_preview": preview,
                    "snapshot_before": snapshot,
                    "execution_result": None,
                    "verification_data": None,
                    "approved_by": None,
                    "approved_at": None,
                }
            )
            self._audit(
                company_id=company_id,
                action_id=action_id,
                actor=actor,
                tool_name=tool.name,
                risk_level="HIGH",
                dry_run=False,
                params=clean_params,
                result={"queued_for_admin_approval": True, "action_id": action_id},
                status="PENDING_APPROVAL",
            )
            return {
                "status": "PENDING_APPROVAL",
                "compliance_status_hint": "Pending Remediation",
                "action_id": action_id,
                "risk_level": "HIGH",
                "tool_name": tool.name,
                "preview": preview,
                "action": action,
            }

        # 5. MEDIUM RISK -> Compatibility Check + Mandatory Snapshot before execution (optional approval)
        if tool.risk_level == "MEDIUM":
            compat = tool.compatibility_fn(self.adapter, company_id, validated) if tool.compatibility_fn else {"compatible": True}
            if not compat.get("compatible", False):
                self._audit(
                    company_id=company_id,
                    action_id=None,
                    actor=actor,
                    tool_name=tool.name,
                    risk_level="MEDIUM",
                    dry_run=False,
                    params=clean_params,
                    result=compat,
                    status="BLOCKED_INCOMPATIBLE",
                )
                return {"status": "BLOCKED_INCOMPATIBLE", "tool_name": tool.name, "compatibility": compat}

            snapshot = tool.snapshot_fn(self.adapter, company_id, validated) if tool.snapshot_fn else None
            preview = tool.handler(self.adapter, company_id, validated, True)
            action_id = str(uuid4())

            if require_medium_approval:
                action = self.store.save_remediation_action(
                    {
                        "action_id": action_id,
                        "company_id": company_id,
                        "assessment_run_id": assessment_run_id,
                        "control_id": control_id,
                        "tool_name": tool.name,
                        "tool_params": clean_params,
                        "risk_level": "MEDIUM",
                        "approval_status": "PENDING_APPROVAL",
                        "dry_run_preview": {**preview, "compatibility": compat},
                        "snapshot_before": snapshot,
                        "execution_result": None,
                        "verification_data": None,
                    }
                )
                self._audit(
                    company_id=company_id,
                    action_id=action_id,
                    actor=actor,
                    tool_name=tool.name,
                    risk_level="MEDIUM",
                    dry_run=False,
                    params=clean_params,
                    result={"queued_for_approval": True, "action_id": action_id},
                    status="PENDING_APPROVAL",
                )
                return {
                    "status": "PENDING_APPROVAL",
                    "compliance_status_hint": "Pending Remediation",
                    "action_id": action_id,
                    "risk_level": "MEDIUM",
                    "tool_name": tool.name,
                    "compatibility": compat,
                    "snapshot_before": snapshot,
                    "action": action,
                }

            result = tool.handler(self.adapter, company_id, validated, False)
            action = self.store.save_remediation_action(
                {
                    "action_id": action_id,
                    "company_id": company_id,
                    "assessment_run_id": assessment_run_id,
                    "control_id": control_id,
                    "tool_name": tool.name,
                    "tool_params": clean_params,
                    "risk_level": "MEDIUM",
                    "approval_status": "EXECUTED",
                    "dry_run_preview": preview,
                    "snapshot_before": snapshot,
                    "execution_result": result,
                    "verification_data": None,
                    "approved_by": actor,
                    "approved_at": utc_now_iso(),
                }
            )
            self._audit(
                company_id=company_id,
                action_id=action_id,
                actor=actor,
                tool_name=tool.name,
                risk_level="MEDIUM",
                dry_run=False,
                params=clean_params,
                result=result,
                status="EXECUTED",
            )
            return {
                "status": "EXECUTED",
                "action_id": action_id,
                "risk_level": "MEDIUM",
                "tool_name": tool.name,
                "compatibility": compat,
                "snapshot_before": snapshot,
                "result": result,
                "action": action,
            }

        # 6. LOW RISK -> Auto-execute (Inspect / Notify / Assign Training / Create Ticket)
        result = tool.handler(self.adapter, company_id, validated, False)
        is_remediation = not tool.name.startswith("inspect_")
        action_id = None
        action = None
        if is_remediation:
            action_id = str(uuid4())
            action = self.store.save_remediation_action(
                {
                    "action_id": action_id,
                    "company_id": company_id,
                    "assessment_run_id": assessment_run_id,
                    "control_id": control_id,
                    "tool_name": tool.name,
                    "tool_params": clean_params,
                    "risk_level": "LOW",
                    "approval_status": "AUTO_APPROVED",
                    "dry_run_preview": None,
                    "snapshot_before": None,
                    "execution_result": result,
                    "verification_data": None,
                    "approved_by": actor,
                    "approved_at": utc_now_iso(),
                }
            )
        self._audit(
            company_id=company_id,
            action_id=action_id,
            actor=actor,
            tool_name=tool.name,
            risk_level="LOW",
            dry_run=False,
            params=clean_params,
            result=result,
            status="EXECUTED",
        )
        return {
            "status": "EXECUTED",
            "action_id": action_id,
            "risk_level": "LOW",
            "tool_name": tool.name,
            "result": result,
            "action": action,
        }

    def approve_and_execute(self, company_id: str, action_id: str, admin_actor: str) -> dict[str, Any]:
        """Human-in-the-loop Admin approval gateway for HIGH / MEDIUM pending remediation actions."""
        action = self.store.get_remediation_action(company_id, action_id)
        if not action:
            raise KeyError(f"Remediation action not found: {action_id}")
        if action["approval_status"] != "PENDING_APPROVAL":
            raise ValueError(f"Action {action_id} is in state {action['approval_status']}, not PENDING_APPROVAL.")

        tool = self._tools[action["tool_name"]]
        validated = tool.param_schema.model_validate(action["tool_params"])

        # Refresh snapshot immediately before execution so rollback reflects exact pre-change state
        snapshot = tool.snapshot_fn(self.adapter, company_id, validated) if tool.snapshot_fn else action.get("snapshot_before")
        result = tool.handler(self.adapter, company_id, validated, False)
        updated = self.store.save_remediation_action(
            {
                **action,
                "approval_status": "EXECUTED",
                "snapshot_before": snapshot,
                "execution_result": result,
                "approved_by": admin_actor,
                "approved_at": utc_now_iso(),
            }
        )
        self._audit(
            company_id=company_id,
            action_id=action_id,
            actor=f"admin:{admin_actor}",
            tool_name=tool.name,
            risk_level=tool.risk_level,
            dry_run=False,
            params=action["tool_params"],
            result=result,
            status="APPROVED_AND_EXECUTED",
        )
        return {"status": "EXECUTED", "action": updated, "result": result}

    def reject_action(self, company_id: str, action_id: str, admin_actor: str, reason: str) -> dict[str, Any]:
        action = self.store.get_remediation_action(company_id, action_id)
        if not action:
            raise KeyError(f"Remediation action not found: {action_id}")
        if action["approval_status"] != "PENDING_APPROVAL":
            raise ValueError(f"Action {action_id} cannot be rejected from state {action['approval_status']}.")
        updated = self.store.save_remediation_action(
            {
                **action,
                "approval_status": "REJECTED",
                "execution_result": {"rejected_reason": reason},
                "approved_by": admin_actor,
                "approved_at": utc_now_iso(),
            }
        )
        self._audit(
            company_id=company_id,
            action_id=action_id,
            actor=f"admin:{admin_actor}",
            tool_name=action["tool_name"],
            risk_level=action["risk_level"],
            dry_run=False,
            params=action["tool_params"],
            result={"rejected_reason": reason},
            status="REJECTED",
        )
        return {"status": "REJECTED", "action": updated}

    def rollback_action(self, company_id: str, action_id: str, actor: str) -> dict[str, Any]:
        """Restore system state from snapshot_before if remediation causes regression."""
        action = self.store.get_remediation_action(company_id, action_id)
        if not action:
            raise KeyError(f"Remediation action not found: {action_id}")
        snapshot = action.get("snapshot_before")
        if not snapshot:
            raise ValueError(f"Action {action_id} has no snapshot_before available for rollback.")
        rb_res = self.adapter.rollback_snapshot(company_id, snapshot)
        updated = self.store.save_remediation_action(
            {
                **action,
                "approval_status": "ROLLED_BACK",
                "execution_result": {**(action.get("execution_result") or {}), "rollback": rb_res},
            }
        )
        self._audit(
            company_id=company_id,
            action_id=action_id,
            actor=actor,
            tool_name=action["tool_name"],
            risk_level=action["risk_level"],
            dry_run=False,
            params={"rollback_action_id": action_id},
            result=rb_res,
            status="ROLLED_BACK",
        )
        return {"status": "ROLLED_BACK", "rollback": rb_res, "action": updated}
