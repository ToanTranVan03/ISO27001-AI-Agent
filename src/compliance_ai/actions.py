from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Connection, text
from sqlalchemy.engine import RowMapping

from compliance_ai.assessments import latest_policy, load_run, stable_hash
from compliance_ai.asset_return import LOCAL_CALENDAR, RECEIPT_JOIN, return_due_date
from compliance_ai.catalog import Policy
from compliance_ai.nda import (
    NdaDocument,
    NdaRequest,
    acknowledged,
    current_document,
    scoped_request,
)

Tool = Literal[
    "disable_sim_account",
    "revoke_sim_grants",
    "request_asset_return",
    "assign_training",
    "request_nda_signature",
    "request_mfa_enrollment",
    "apply_sim_baseline",
    "apply_sim_patch",
]


@dataclass(frozen=True)
class ToolSpec:
    kind: str
    risk: Literal["high", "medium", "low"]
    recovery: str


TOOLS: dict[str, ToolSpec] = {
    "request_mfa_enrollment": ToolSpec(
        "account", "low", "Đối chiếu trạng thái tại nguồn định danh."
    ),
    "apply_sim_baseline": ToolSpec("endpoint", "medium", "Khôi phục hồ sơ cấu hình mô phỏng."),
    "apply_sim_patch": ToolSpec("endpoint", "medium", "Dùng snapshot trình mô phỏng để phục hồi."),
    "disable_sim_account": ToolSpec("account", "high", "Đối chiếu lại HR và tạo yêu cầu phục hồi."),
    "revoke_sim_grants": ToolSpec(
        "account", "high", "Đối chiếu danh sách quyền trước khi cấp lại."
    ),
    "request_asset_return": ToolSpec("asset", "low", "Đóng phiếu sau khi kiểm tra biên bản."),
    "assign_training": ToolSpec("training", "low", "Nhân viên có thể yêu cầu xem lại bài."),
    "request_nda_signature": ToolSpec(
        "training", "low", "Chỉ nhân viên tự xác nhận bản cam kết mô phỏng."
    ),
}


class Plan(BaseModel):
    company_id: UUID
    target_id: UUID
    tool: Tool
    revision: int
    policy_version: int
    expires_at: datetime
    risk: Literal["high", "medium", "low"]
    recovery: str
    execution_mode: Literal["SIMULATION"] = "SIMULATION"
    changes: dict[str, object] | None = None
    nda_document: NdaDocument | None = None


class Action(BaseModel):
    id: UUID
    run_id: UUID
    finding_id: UUID
    requested_by: UUID
    plan: Plan
    plan_hash: str
    state: str
    approved_by: UUID | None
    approval_expires_at: datetime | None
    executed_at: datetime | None
    result: dict[str, object] | None
    verification: dict[str, object] | None


class Proof(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class Decision(Proof):
    approve: bool = Field(strict=True)


def show(row: RowMapping) -> Action:
    return Action.model_validate(dict(row))


def resource(connection: Connection, tenant: UUID, target: UUID, *, lock=False) -> RowMapping:
    query = (
        """
        SELECT r.id, r.kind, r.state, r.revision, r.updated_at,
               e.employment_status, e.termination_effective_at, receipt.id AS receipt_id,
               receipt.received_at AS received_at
        FROM app_data.sim_resources r JOIN app_data.employees e
          ON (e.company_id,e.id) = (r.company_id,r.employee_id)
        """
        + RECEIPT_JOIN
        + """
        WHERE r.company_id = :tenant AND r.id = :target
    """
    )
    if lock:
        query += " FOR UPDATE OF r,e"
    row = connection.execute(text(query), {"tenant": tenant, "target": target}).mappings().first()
    if row is None:
        raise LookupError("Không tìm thấy đối tượng mô phỏng.")
    return row


def find_action(connection: Connection, tenant: UUID, action: UUID, *, lock=False) -> RowMapping:
    statement = """
        SELECT * FROM app_data.sim_actions WHERE company_id = :tenant AND id = :id
    """
    row = (
        connection.execute(
            text(statement + (" FOR UPDATE" if lock else "")), {"tenant": tenant, "id": action}
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise LookupError("Không tìm thấy hành động.")
    return row


def audit(connection: Connection, tenant: UUID, actor: UUID, action: UUID, event: str) -> None:
    connection.execute(
        text("""
        INSERT INTO app_data.audit_events (company_id,id,actor_id,event_type,target_id,detail)
        VALUES (:tenant,:id,:actor,:event,:action,CAST('{}' AS jsonb))
    """),
        {"tenant": tenant, "id": uuid4(), "actor": actor, "event": event, "action": action},
    )


def plan_action(
    connection: Connection,
    tenant: UUID,
    actor: UUID,
    run_id: UUID,
    finding_id: UUID,
) -> Action:
    run = load_run(connection, tenant, run_id)
    finding = next((item for item in run.findings if item.id == finding_id), None) if run else None
    if run is None or finding is None:
        raise LookupError("Không tìm thấy phát hiện.")
    if finding.proposed_tool not in TOOLS:
        raise ValueError("Phát hiện này cần xem xét thủ công.")
    target = resource(connection, tenant, finding.target_id)
    tool = TOOLS[finding.proposed_tool]
    if target["kind"] != tool.kind or target["revision"] != finding.observed["revision"]:
        raise ValueError("Bằng chứng đã đổi. Hãy đánh giá lại.")
    policy = latest_policy(connection, tenant)
    if policy is None or policy.version != run.policy_version:
        raise ValueError("Phiên bản chính sách đã đổi. Hãy đánh giá lại.")
    if finding.proposed_tool == "request_nda_signature" and scoped_request(
        target["state"], tenant, target["id"], policy.version
    ):
        raise ValueError("Đã có yêu cầu NDA cho phiên bản này. Hãy mở hành động hiện có.")
    changes: dict[str, object] | None = None
    if finding.proposed_tool == "apply_sim_baseline":
        changes = {"screen_lock_seconds": policy.screen_lock_max_seconds}
    if finding.proposed_tool == "apply_sim_patch":
        installed = target["state"].get("patches")
        if not isinstance(installed, list) or any(not isinstance(x, str) for x in installed):
            raise ValueError("Thiếu kiểm kê bản vá.")
        changes = {"patches": sorted({*installed, "SIM-001"})}
    plan = Plan.model_validate(
        {
            "company_id": tenant,
            "target_id": finding.target_id,
            "tool": finding.proposed_tool,
            "revision": target["revision"],
            "policy_version": run.policy_version,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
            "risk": tool.risk,
            "recovery": tool.recovery,
            "changes": changes,
            "nda_document": current_document()
            if finding.proposed_tool == "request_nda_signature"
            else None,
        }
    )
    params = {
        "tenant": tenant,
        "id": uuid4(),
        "run": run_id,
        "finding": finding_id,
        "target": finding.target_id,
        "actor": actor,
        "doc": plan.model_dump_json(),
        "digest": stable_hash(plan.model_dump(mode="json", exclude_none=True)),
        "state": "WAITING_APPROVAL" if tool.risk != "low" else "PROPOSED",
    }
    connection.execute(
        text("""
        INSERT INTO app_data.sim_actions (
            company_id,id,run_id,finding_id,target_id,requested_by,plan,plan_hash,state
        ) VALUES (:tenant,:id,:run,:finding,:target,:actor,CAST(:doc AS jsonb),:digest,:state)
        ON CONFLICT (company_id,run_id,finding_id) DO NOTHING
    """),
        params,
    )
    row = (
        connection.execute(
            text("""
        SELECT * FROM app_data.sim_actions WHERE company_id=:tenant AND run_id=:run
            AND finding_id=:finding
    """),
            params,
        )
        .mappings()
        .one()
    )
    return show(row)


def verify_plan(action: Action, proof: Proof) -> None:
    if action.plan_hash != proof.plan_hash or action.plan_hash != stable_hash(
        action.plan.model_dump(mode="json", exclude_none=True)
    ):
        raise ValueError("Mã xác nhận kế hoạch không khớp.")


def decide(
    connection: Connection,
    tenant: UUID,
    actor: UUID,
    identifier: UUID,
    payload: Decision,
) -> Action:
    action = show(find_action(connection, tenant, identifier, lock=True))
    verify_plan(action, payload)
    if action.state != "WAITING_APPROVAL" or actor == action.requested_by:
        raise ValueError("Cần người duyệt độc lập và yêu cầu đang chờ.")
    target = resource(connection, tenant, action.plan.target_id, lock=True)
    policy = latest_policy(connection, tenant)
    now = datetime.now(UTC)
    if payload.approve:
        gate, reason = inspect_gate(action, tenant, target, policy, now)
        if gate not in ("NEEDS_APPROVAL", "EXPIRED"):
            raise ValueError(reason)
    state = (
        "EXPIRED"
        if now >= action.plan.expires_at
        else ("APPROVED" if payload.approve else "REJECTED")
    )
    connection.execute(
        text("""
        UPDATE app_data.sim_actions SET state=:state, approved_by=:approver,
            approval_expires_at=:until
        WHERE company_id=:tenant AND id=:id
    """),
        {
            "tenant": tenant,
            "id": identifier,
            "state": state,
            "approver": actor if state == "APPROVED" else None,
            "until": min(now + timedelta(minutes=15), action.plan.expires_at)
            if state == "APPROVED"
            else None,
        },
    )
    audit(connection, tenant, actor, identifier, state)
    return show(find_action(connection, tenant, identifier))


def postcondition(plan: Plan, state: dict[str, object]) -> bool:
    tool = plan.tool
    if tool == "apply_sim_baseline":
        return plan.changes is not None and (
            state.get("screen_lock_seconds") == plan.changes.get("screen_lock_seconds")
        )
    if tool == "apply_sim_patch":
        return plan.changes is not None and state.get("patches") == plan.changes.get("patches")
    if tool == "disable_sim_account":
        return state.get("enabled") is False
    if tool == "revoke_sim_grants":
        return state.get("grants") == []
    if tool == "request_asset_return":
        return state.get("returned") is True and state.get("custody") == "asset_desk"
    if tool == "request_mfa_enrollment":
        return state.get("mfa_registered") is True and state.get("mfa_enforced") is True
    if tool == "request_nda_signature":
        request = scoped_request(state, plan.company_id, plan.target_id, plan.policy_version)
        return (
            acknowledged(request) and request is not None and request.document == plan.nda_document
        )
    return state.get("passed_retest") is True


GateState = Literal["READY", "NEEDS_APPROVAL", "EXPIRED", "BLOCKED"]


class Preview(BaseModel):
    state: GateState
    reason: str
    target_id: UUID
    revision: int
    risk: Literal["low", "medium", "high"]
    changes: dict[str, object] | None
    plan_hash: str


def inspect_gate(
    action: Action, tenant: UUID, target: RowMapping, policy: Policy | None, now: datetime
) -> tuple[GateState, str]:
    plan = action.plan
    previous = target["state"]
    if action.state not in ("PROPOSED", "WAITING_APPROVAL", "APPROVED"):
        return "BLOCKED", "Hành động đã kết thúc hoặc đã thực thi."
    expired = now >= plan.expires_at or (
        action.approval_expires_at is not None and now >= action.approval_expires_at
    )
    valid = (
        plan.company_id == tenant
        and plan.execution_mode == "SIMULATION"
        and target["kind"] == TOOLS[plan.tool].kind
        and target["revision"] == plan.revision
        and policy is not None
        and plan.policy_version == policy.version
        and (plan.tool != "request_nda_signature" or plan.nda_document == current_document())
        and (
            plan.tool != "request_asset_return"
            or (
                target["employment_status"] == "terminated"
                and target["termination_effective_at"] is not None
                and now >= target["termination_effective_at"]
                and previous.get("returned") is False
                and "return_receipt" in previous
                and previous["return_receipt"] is None
            )
        )
        and (
            target["kind"] != "account"
            or (
                plan.tool == "request_mfa_enrollment"
                and target["employment_status"] in ("active", "transfer")
                and previous.get("enabled") is True
                and previous.get("protected") is False
                and previous.get("mfa_registered") is False
                and type(previous.get("mfa_enforced")) is bool
            )
            or (
                plan.tool in ("disable_sim_account", "revoke_sim_grants")
                and previous.get("protected") is False
                and target["employment_status"] == "terminated"
                and target["termination_effective_at"] is not None
                and now
                >= target["termination_effective_at"]
                + timedelta(hours=policy.termination_access_hours)
            )
        )
    )
    if expired:
        return "EXPIRED", "Kế hoạch hoặc lượt phê duyệt đã hết hạn."
    if not valid:
        return "BLOCKED", "Đích, phiên bản, chính sách hoặc điều kiện thực thi đã thay đổi."
    if plan.risk == "medium" and (not plan.changes or any(k not in previous for k in plan.changes)):
        return "BLOCKED", "Thiếu dữ liệu để tạo snapshot phục hồi."
    if plan.risk != "low":
        if action.state == "WAITING_APPROVAL":
            return "NEEDS_APPROVAL", "Cần admin khác người lập kế hoạch phê duyệt."
        if (
            action.state != "APPROVED"
            or action.approved_by in (None, action.requested_by)
            or action.approval_expires_at is None
        ):
            return "BLOCKED", "Chưa có lượt phê duyệt hợp lệ."
    elif action.state != "PROPOSED":
        return "BLOCKED", "Trạng thái không cho phép thực thi."
    return "READY", "Điều kiện thực thi hiện tại đã đạt."


def preview_action(connection: Connection, tenant: UUID, identifier: UUID, proof: Proof) -> Preview:
    action = show(find_action(connection, tenant, identifier))
    verify_plan(action, proof)
    target = resource(connection, tenant, action.plan.target_id)
    gate, reason = inspect_gate(
        action, tenant, target, latest_policy(connection, tenant), datetime.now(UTC)
    )
    return Preview(
        state=gate,
        reason=reason,
        target_id=action.plan.target_id,
        revision=target["revision"],
        risk=action.plan.risk,
        changes=action.plan.changes,
        plan_hash=action.plan_hash,
    )


def execute(
    connection: Connection,
    tenant: UUID,
    actor: UUID,
    identifier: UUID,
    proof: Proof,
    key: str,
) -> Action:
    row = find_action(connection, tenant, identifier, lock=True)
    action = show(row)
    verify_plan(action, proof)
    if row["execution_key"] == key:
        return action
    if row["execution_key"] is not None:
        raise ValueError("Hành động đã được thực thi bằng khóa khác.")
    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock))"),
        {
            "lock": f"execution/{tenant}/{key}",
        },
    )
    if connection.scalar(
        text("""
        SELECT 1 FROM app_data.sim_actions WHERE company_id=:tenant AND execution_key=:key
    """),
        {"tenant": tenant, "key": key},
    ):
        raise ValueError("Khóa thực thi đã dùng cho hành động khác.")
    plan = action.plan
    if plan.risk != "low" and action.state != "APPROVED":
        raise ValueError("Cần phê duyệt trước khi thực thi.")
    if plan.risk == "low" and action.state != "PROPOSED":
        raise ValueError("Trạng thái không cho phép thực thi.")
    target = resource(connection, tenant, plan.target_id, lock=True)
    policy = latest_policy(connection, tenant)
    now = datetime.now(UTC)
    gate, _ = inspect_gate(action, tenant, target, policy, now)
    previous = dict(target["state"])
    updated = dict(previous)
    snapshot = None
    if gate == "EXPIRED":
        state = "EXPIRED"
    elif gate != "READY":
        state = "FAILED"
    else:
        if plan.risk == "medium":
            snapshot = {field: previous[field] for field in plan.changes or {}}
        state = "SUCCEEDED" if plan.risk != "low" else "WAITING_EXTERNAL"
        if plan.tool in ("apply_sim_baseline", "apply_sim_patch"):
            updated.update(plan.changes or {})
        elif plan.tool == "disable_sim_account":
            updated["enabled"] = False
        elif plan.tool == "revoke_sim_grants":
            updated["grants"] = []
        elif plan.tool == "request_asset_return":
            updated["return_ticket"] = str(identifier)
        elif plan.tool == "request_mfa_enrollment":
            updated["mfa_request"] = str(identifier)
        elif plan.tool == "request_nda_signature":
            updated["nda_request"] = NdaRequest(
                id=identifier,
                company_id=tenant,
                target_id=plan.target_id,
                policy_version=plan.policy_version,
                document=current_document(),
                requested_at=now,
            ).model_dump(mode="json")
        elif updated.get("assignment") is None:
            updated["assignment"] = {"id": str(identifier), "status": "ASSIGNED"}
        connection.execute(
            text("""
            UPDATE app_data.sim_resources SET state=CAST(:doc AS jsonb),revision=revision+1,
                updated_at=:now WHERE company_id=:tenant AND id=:target
        """),
            {"tenant": tenant, "target": plan.target_id, "now": now, "doc": dumps_json(updated)},
        )
    connection.execute(
        text("""
        UPDATE app_data.sim_actions SET state=:state, executed_at=:now, execution_key=:key,
            result=CAST(:result AS jsonb)
        WHERE company_id=:tenant AND id=:id
    """),
        {
            "tenant": tenant,
            "id": identifier,
            "state": state,
            "now": now,
            "key": key,
            "result": dumps_json(
                {
                    "previous_revision": target["revision"],
                    "backend": "SIMULATION",
                    "snapshot": snapshot,
                }
            ),
        },
    )
    audit(connection, tenant, actor, identifier, state)
    return show(find_action(connection, tenant, identifier))


def dumps_json(value: object) -> str:
    from json import dumps

    return dumps(value, ensure_ascii=False)


def verify(connection: Connection, tenant: UUID, actor: UUID, identifier: UUID) -> Action:
    action = show(find_action(connection, tenant, identifier, lock=True))
    if action.state == "VERIFIED":
        return action
    if action.state not in ("SUCCEEDED", "WAITING_EXTERNAL", "VERIFICATION_FAILED"):
        raise ValueError("Hành động chưa thực thi hoặc không thể xác minh.")
    target = resource(connection, tenant, action.plan.target_id)
    policy = latest_policy(connection, tenant)
    fresh = target["revision"] > action.plan.revision and (
        action.executed_at is not None and target["updated_at"] >= action.executed_at
    )
    if action.plan.tool == "request_asset_return":
        fresh = (
            fresh
            and target["receipt_id"] is not None
            and action.executed_at is not None
            and target["received_at"] >= action.executed_at
            and target["termination_effective_at"] is not None
            and target["termination_effective_at"] <= target["received_at"] <= datetime.now(UTC)
            and target["state"].get("return_ticket") == str(identifier)
        )
    if action.plan.tool == "request_nda_signature":
        request = scoped_request(
            target["state"], tenant, action.plan.target_id, action.plan.policy_version
        )
        fresh = fresh and request is not None and request.id == identifier
    if action.plan.tool == "request_mfa_enrollment":
        observation = target["state"].get("mfa_observation") or {}
        fresh = (
            fresh
            and isinstance(observation, dict)
            and observation.get("request_id") == str(identifier)
            and observation.get("source") == "synthetic_identity_provider"
            and isinstance(observation.get("id"), str)
            and target["state"].get("mfa_request") == str(identifier)
            and observation.get("registered") is True
            and observation.get("enforced") is True
            and target["employment_status"] in ("active", "transfer")
            and target["state"].get("enabled") is True
        )
    state = (
        "VERIFIED"
        if fresh
        and policy is not None
        and (
            policy.version == action.plan.policy_version
            and postcondition(action.plan, target["state"])
        )
        else "WAITING_EXTERNAL"
        if action.plan.risk == "low"
        else "VERIFICATION_FAILED"
    )
    evidence = {
        "revision": target["revision"],
        "fresh": fresh,
        "observed_at": datetime.now(UTC).isoformat(),
        "evidence_id": str(uuid5(action.plan.target_id, f"state/{target['revision']}")),
    }
    if (
        action.plan.tool == "request_nda_signature"
        and state == "VERIFIED"
        and request
        and request.receipt
    ):
        evidence["receipt_id"] = str(request.receipt.evidence_id)
    if action.plan.tool == "request_mfa_enrollment" and state == "VERIFIED":
        evidence["identity_event_id"] = observation["id"]
    if action.plan.tool == "request_asset_return" and state == "VERIFIED" and policy is not None:
        evidence["receipt_id"] = str(target["receipt_id"])
        evidence["source"] = "synthetic_asset_desk"
        due = return_due_date(target["termination_effective_at"], policy.asset_return_business_days)
        evidence["due_date"] = due.isoformat()
        evidence["return_timing"] = (
            "ON_TIME" if target["received_at"].astimezone(LOCAL_CALENDAR).date() <= due else "LATE"
        )
    connection.execute(
        text("""
        UPDATE app_data.sim_actions SET state=:state, verification=CAST(:doc AS jsonb)
        WHERE company_id=:tenant AND id=:id
    """),
        {"tenant": tenant, "id": identifier, "state": state, "doc": dumps_json(evidence)},
    )
    audit(connection, tenant, actor, identifier, state)
    return show(find_action(connection, tenant, identifier))


def rollback(
    connection: Connection,
    tenant: UUID,
    actor: UUID,
    identifier: UUID,
    proof: Proof,
) -> Action:
    action = show(find_action(connection, tenant, identifier, lock=True))
    verify_plan(action, proof)
    if actor != action.approved_by:
        raise ValueError("Chỉ người đã duyệt được phục hồi thay đổi endpoint có snapshot.")
    if action.state == "ROLLED_BACK":
        return action
    plan = action.plan
    if (
        plan.risk != "medium"
        or not plan.changes
        or action.state not in ("SUCCEEDED", "VERIFIED", "VERIFICATION_FAILED")
    ):
        raise ValueError("Chỉ người đã duyệt được phục hồi thay đổi endpoint có snapshot.")
    snapshot = (action.result or {}).get("snapshot")
    if not isinstance(snapshot, dict) or snapshot.keys() != plan.changes.keys():
        raise ValueError("Thiếu snapshot có thể phục hồi.")
    target = resource(connection, tenant, plan.target_id, lock=True)
    policy = latest_policy(connection, tenant)
    if (
        target["kind"] != "endpoint"
        or target["revision"] != plan.revision + 1
        or not postcondition(plan, target["state"])
        or policy is None
        or policy.version != plan.policy_version
    ):
        raise ValueError("Trạng thái hoặc chính sách đã đổi. Không ghi đè thay đổi mới.")
    updated = target["state"] | snapshot
    connection.execute(
        text("""
          UPDATE app_data.sim_resources SET state=CAST(:doc AS jsonb),revision=revision+1,
            updated_at=now() WHERE company_id=:tenant AND id=:target
        """),
        {"tenant": tenant, "target": plan.target_id, "doc": dumps_json(updated)},
    )
    restored = resource(connection, tenant, plan.target_id)
    if any(restored["state"].get(key) != value for key, value in snapshot.items()):
        raise ValueError("Đối chiếu snapshot không khớp. Giao dịch đã hủy.")
    evidence = {
        "restored": True,
        "revision": restored["revision"],
        "observed_at": datetime.now(UTC).isoformat(),
        "evidence_id": str(uuid5(plan.target_id, f"state/{restored['revision']}")),
    }
    connection.execute(
        text("""
        UPDATE app_data.sim_actions SET state='ROLLED_BACK',verification=CAST(:doc AS jsonb)
        WHERE company_id=:tenant AND id=:id
    """),
        {"tenant": tenant, "id": identifier, "doc": dumps_json(evidence)},
    )
    audit(connection, tenant, actor, identifier, "ROLLED_BACK")
    return show(find_action(connection, tenant, identifier))
