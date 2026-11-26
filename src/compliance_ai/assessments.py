from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from json import dumps
from typing import Literal, TypedDict
from uuid import UUID, uuid4, uuid5

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Connection, text
from sqlalchemy.engine import RowMapping

from compliance_ai.asset_return import LOCAL_CALENDAR, RECEIPT_JOIN, return_due_date
from compliance_ai.catalog import Criterion, Pillar, Policy, research_catalog
from compliance_ai.nda import acknowledged, scoped_request
from compliance_ai.rag import Citation, assessment_citations
from compliance_ai.rules import Instance, Observation, Outcome, Status, evaluate, score

Mode = Literal["offboarding", "scenarios"]
CaseValue = bool | int | list[bool | int]
SOURCE: Literal["research_rubric"] = "research_rubric"


class ScanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Mode = "offboarding"
    employee_code: str = Field(default="NV015", pattern=r"^NV\d{3}$")


class Finding(BaseModel):
    id: UUID
    criterion_id: str
    control_ids: list[str]
    target_id: UUID
    status: Status
    evidence_ids: tuple[str, ...]
    source: Literal["research_rubric"] = SOURCE
    missing_evidence: tuple[str, ...]
    explanation: str
    observed: dict[str, object]
    proposed_tool: str | None = None


class Assessment(BaseModel):
    id: UUID
    company_id: UUID
    policy_version: int
    scope: ScanInput
    status: Literal["COMPLETED"] = "COMPLETED"
    execution_mode: Literal["SIMULATION"] = "SIMULATION"
    assessed_at: datetime
    findings: list[Finding]
    scores: dict[str, object]
    workflow_steps: list[str] = Field(default_factory=list)
    citations_by_control: dict[str, list[Citation]] | None = None


def stable_hash(value: object) -> str:
    return sha256(dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def latest_policy(connection: Connection, tenant: UUID) -> Policy | None:
    value = connection.scalar(
        text("""
        SELECT document FROM app_data.policy_versions WHERE company_id = :tenant
          AND effective_at <= now() ORDER BY version DESC LIMIT 1
    """),
        {"tenant": tenant},
    )
    return Policy.model_validate(value) if value is not None else None


def case_result(
    criterion: Criterion,
    policy: Policy,
    case_id: UUID,
    facts: dict[str, CaseValue],
    observed_at: datetime,
    exclusion: str | None,
) -> Outcome:
    if exclusion:
        return Outcome(Status.NA, rationale=exclusion)
    observations = [
        Observation(str(uuid5(case_id, f"{key}/{index}")), key, value, observed_at)
        for key, values in facts.items()
        for index, value in enumerate(values if isinstance(values, list) else [values])
    ]
    return evaluate(criterion, policy, observations, observed_at)


def record_finding(
    run: UUID,
    criterion: Criterion,
    target: UUID,
    result: Outcome,
    facts: dict[str, object],
    tool: str | None = None,
) -> Finding:
    return Finding(
        id=uuid5(run, f"{criterion.id}/{target}"),
        criterion_id=criterion.id,
        control_ids=criterion.control_ids,
        target_id=target,
        status=result.status,
        evidence_ids=result.evidence_ids,
        missing_evidence=result.missing_evidence,
        explanation=result.rationale,
        observed=facts,
        proposed_tool=tool,
    )


def scenario_rows(connection: Connection, tenant: UUID, policy: Policy) -> list[RowMapping]:
    return list(
        connection.execute(
            text("""
        SELECT id, criterion_id, evidence, observed_at, exclusion_reason, scenario_id
        FROM app_data.sim_cases WHERE company_id = :tenant AND policy_version = :policy
        ORDER BY scenario_id, id
    """),
            {"tenant": tenant, "policy": policy.version},
        ).mappings()
    )


def scenario_findings(
    rows: list[RowMapping],
    run: UUID,
    policy: Policy,
    criteria: dict[str, Criterion],
    pillar: Pillar,
) -> list[Finding]:
    return [
        record_finding(
            run,
            criteria[row["criterion_id"]],
            row["id"],
            case_result(
                criteria[row["criterion_id"]],
                policy,
                row["id"],
                row["evidence"],
                row["observed_at"],
                row["exclusion_reason"],
            ),
            {"scenario_id": row["scenario_id"], "facts": row["evidence"]},
        )
        for row in rows
        if criteria[row["criterion_id"]].primary_pillar == pillar
    ]


def employee_resources(
    connection: Connection,
    tenant: UUID,
    code: str,
) -> tuple[RowMapping, dict[str, RowMapping]] | None:
    employee = (
        connection.execute(
            text("""
        SELECT id, employment_status, termination_effective_at, revision
        FROM app_data.employees WHERE company_id = :tenant AND code = :code
    """),
            {"tenant": tenant, "code": code},
        )
        .mappings()
        .one_or_none()
    )
    if employee is None:
        return None
    resources = connection.execute(
        text(
            """
        SELECT r.company_id, r.id, r.kind, r.state, r.revision, r.updated_at,
               receipt.id AS receipt_id, receipt.received_at, a.id AS pending_action,
               (a.plan->>'policy_version')::integer AS request_version
        FROM app_data.sim_resources r
        """
            + RECEIPT_JOIN
            + """
        LEFT JOIN app_data.sim_actions a ON a.company_id=r.company_id AND a.target_id=r.id
            AND a.id::text=CASE r.kind WHEN 'account' THEN r.state->>'mfa_request'
                                       WHEN 'asset' THEN r.state->>'return_ticket' END
            AND a.state='WAITING_EXTERNAL'
        WHERE r.company_id = :tenant AND r.employee_id = :employee
    """
        ),
        {"tenant": tenant, "employee": employee["id"]},
    ).mappings()
    return employee, {row["kind"]: row for row in resources}


def offboarding_findings(
    run: UUID,
    employee: RowMapping,
    resources: dict[str, RowMapping],
    policy: Policy,
    criteria: dict[str, Criterion],
    now: datetime,
    pillar: Pillar,
) -> list[Finding]:
    termination = employee["termination_effective_at"]
    offboarded = employee["employment_status"] == "terminated" and termination is not None
    hr = str(uuid5(employee["id"], f"hr/{employee['revision']}"))
    overdue = offboarded and now >= termination + timedelta(hours=policy.termination_access_hours)
    result = []
    definitions = (
        ("H09", "account", "enabled", "disable_sim_account", overdue),
        ("M01", "account", "grants", "revoke_sim_grants", overdue),
        (
            "D02",
            "asset",
            "return_receipt",
            "request_asset_return",
            offboarded and now >= termination,
        ),
        ("H06", "training", "nda_signed", "request_nda_signature", True),
        ("H03", "training", "passed_retest", "assign_training", True),
        (
            "S02",
            "account",
            "mfa_enforced",
            "request_mfa_enrollment",
            employee["employment_status"] in ("active", "transfer"),
        ),
        ("S05", "endpoint", "screen_lock_seconds", "apply_sim_baseline", True),
        ("S04", "endpoint", "patches", "apply_sim_patch", True),
    )
    for criterion_id, kind, key, default_tool, applicable in definitions:
        tool: str | None = default_tool
        criterion = criteria[criterion_id]
        if criterion.primary_pillar != pillar:
            continue
        row = resources.get(kind)
        state = row["state"] if row else {}
        target = row["id"] if row else employee["id"]
        facts = {
            "source": kind,
            "revision": row["revision"] if row else None,
            "value": state.get(key),
            "employment_status": employee["employment_status"],
        }
        evidence = (hr, str(uuid5(target, f"state/{row['revision']}"))) if row else (hr,)
        exclusion = policy.scope_exclusions.get(criterion_id)
        value = state.get(key)
        if exclusion or not applicable:
            outcome = Outcome(Status.NA, evidence, rationale=exclusion or "Ngoài phạm vi hiện tại.")
        elif criterion_id == "D02" and row is not None:
            due = return_due_date(termination, policy.asset_return_business_days)
            facts.update(due_date=due.isoformat(), business_days=policy.asset_return_business_days)
            if (
                row["receipt_id"]
                and state.get("returned") is True
                and state.get("custody") == "asset_desk"
                and termination <= row["received_at"] <= now
            ):
                on_time = row["received_at"].astimezone(LOCAL_CALENDAR).date() <= due
                outcome = Outcome(
                    Status.COMPLIANT if on_time else Status.PARTIAL,
                    (*evidence, str(row["receipt_id"])),
                    rationale=f"Kho nhận {'đúng hạn' if on_time else 'trễ hạn'} (hạn {due}).",
                )
                facts["received_at"] = row["received_at"].isoformat()
                facts["return_timing"] = "ON_TIME" if on_time else "LATE"
                tool = None
            elif state.get("returned") is False and key in state and value is None:
                past_due = now.astimezone(LOCAL_CALENDAR).date() > due
                facts["return_timing"] = "OVERDUE" if past_due else "WITHIN_WINDOW"
                outcome = Outcome(
                    Status.NON_COMPLIANT if past_due else Status.UNKNOWN,
                    evidence,
                    ("return_receipt",),
                    f"Chưa có biên nhận, {'đã quá hạn' if past_due else 'còn trong hạn'} {due}.",
                )
            else:
                outcome = Outcome(
                    Status.UNKNOWN,
                    evidence,
                    ("return_receipt",),
                    "Cần đối soát biên nhận của kho và hồ sơ người giữ tài sản.",
                )
            if row["pending_action"] and row["request_version"] == policy.version:
                facts["request_id"] = str(row["pending_action"])
                tool = None
        elif criterion_id == "S02" and row is not None:
            flags = {field: state.get(field) for field in ("mfa_registered", "mfa_enforced")}
            facts.update(flags)
            missing = tuple(field for field, flag in flags.items() if type(flag) is not bool)
            if missing:
                outcome = Outcome(Status.UNKNOWN, evidence, missing, "Thiếu dữ liệu định danh MFA.")
            elif all(flags.values()):
                outcome = Outcome(
                    Status.COMPLIANT, evidence, rationale="MFA đã đăng ký và cưỡng chế."
                )
            elif any(flags.values()):
                outcome = Outcome(Status.PARTIAL, evidence, rationale="MFA mới đạt một điều kiện.")
            else:
                outcome = Outcome(
                    Status.NON_COMPLIANT, evidence, rationale="Chưa đăng ký và cưỡng chế MFA."
                )
            if row["pending_action"] and row["request_version"] == policy.version:
                facts["request_id"] = str(row["pending_action"])
                tool = None
            if (
                flags["mfa_registered"] is not False
                or state.get("enabled") is not True
                or state.get("protected") is not False
            ):
                tool = None
        elif criterion_id == "H06" and row is not None:
            request = scoped_request(state, row["company_id"], target, policy.version)
            if request and acknowledged(request) and request.receipt:
                outcome = Outcome(
                    Status.COMPLIANT,
                    (*evidence, str(request.receipt.evidence_id)),
                    rationale="Có biên nhận của nhân viên cho bản cam kết hiện hành.",
                )
            elif value is False:
                outcome = Outcome(Status.NON_COMPLIANT, evidence, rationale="Chưa xác nhận NDA.")
            else:
                outcome = Outcome(
                    Status.UNKNOWN,
                    evidence,
                    ("nda_receipt",),
                    "Thiếu biên nhận gắn với phiên bản cam kết hiện hành.",
                )
            if request:
                tool = None
                facts["request_id"] = str(request.id)
        elif (
            row is None
            or key not in state
            or (value is None and criterion_id not in ("D02", "H03"))
        ):
            if criterion_id == "H03" and row is not None and "assignment" in state:
                outcome = Outcome(Status.NON_COMPLIANT, evidence, rationale="Chưa có bài đạt.")
            else:
                outcome = Outcome(Status.UNKNOWN, evidence, (key,), "Thiếu bằng chứng nguồn.")
        else:
            if criterion_id in ("H09", "M01"):
                passed = not bool(value)
            elif criterion_id == "S05":
                passed = type(value) is int and 0 < value <= policy.screen_lock_max_seconds
            elif criterion_id == "S04":
                passed = isinstance(value, list) and "SIM-001" in value
            else:
                passed = bool(value)
            outcome = Outcome(
                Status.COMPLIANT if passed else Status.NON_COMPLIANT,
                evidence,
                rationale="Bằng chứng nguồn đạt rubric."
                if passed
                else "Bằng chứng chưa đạt rubric.",
            )
        result.append(
            record_finding(
                run,
                criterion,
                target,
                outcome,
                facts,
                tool
                if outcome.status == Status.NON_COMPLIANT
                or (criterion_id == "D02" and facts.get("return_timing") == "WITHIN_WINDOW")
                or (criterion_id == "S02" and outcome.status == Status.PARTIAL)
                or (criterion_id == "H06" and row is not None and outcome.status == Status.UNKNOWN)
                else None,
            )
        )
    return result


class AssessmentState(TypedDict):
    run: UUID
    observed_at: datetime
    policy: Policy
    criteria: dict[str, Criterion]
    employee: tuple[RowMapping, dict[str, RowMapping]] | None
    scenarios: list[RowMapping]
    findings: list[Finding]
    scores: dict[str, object]
    workflow_steps: list[str]


def specialist(pillar: Pillar):
    def analyze(state: AssessmentState) -> dict[str, object]:
        if state["employee"] is None:
            findings = scenario_findings(
                state["scenarios"],
                state["run"],
                state["policy"],
                state["criteria"],
                pillar,
            )
        else:
            findings = offboarding_findings(
                state["run"],
                *state["employee"],
                state["policy"],
                state["criteria"],
                state["observed_at"],
                pillar,
            )
        return {
            "findings": state["findings"] + findings,
            "workflow_steps": state["workflow_steps"] + [pillar],
        }

    return analyze


def summarize(state: AssessmentState) -> dict[str, object]:
    scores = score(
        [
            Instance(
                state["criteria"][item.criterion_id], str(item.target_id), Outcome(item.status)
            )
            for item in state["findings"]
        ]
    )
    return {"scores": asdict(scores), "workflow_steps": state["workflow_steps"] + ["report"]}


graph_builder = StateGraph(AssessmentState)
graph_builder.add_node("people", specialist("people"))
graph_builder.add_node("hardware", specialist("hardware"))
graph_builder.add_node("software", specialist("software"))
graph_builder.add_node("report", summarize)
graph_builder.add_edge(START, "people")
graph_builder.add_edge("people", "hardware")
graph_builder.add_edge("hardware", "software")
graph_builder.add_edge("software", "report")
graph_builder.add_edge("report", END)
ASSESSMENT_GRAPH = graph_builder.compile()


def run_assessment(
    connection: Connection,
    tenant: UUID,
    actor: UUID,
    scope: ScanInput,
    key: str,
) -> Assessment:
    digest = stable_hash(scope.model_dump())
    params = {"tenant": tenant, "actor": actor, "key": key}
    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock))"),
        {
            "lock": f"scan/{tenant}/{actor}/{key}",
        },
    )
    existing = (
        connection.execute(
            text("""
        SELECT request_hash, document FROM app_data.assessments
        WHERE company_id = :tenant AND actor_id = :actor AND request_key = :key
    """),
            params,
        )
        .mappings()
        .one_or_none()
    )
    if existing:
        if existing["request_hash"] != digest:
            raise ValueError("Khóa yêu cầu đã gắn với phạm vi khác.")
        return Assessment.model_validate(existing["document"])
    policy = latest_policy(connection, tenant)
    if policy is None:
        raise LookupError("Chưa có chính sách mô phỏng.")
    run_id, captured_at = uuid4(), datetime.now(UTC)
    criteria = {criterion.id: criterion for criterion in research_catalog().criteria}
    records = None
    scenarios: list[RowMapping] = []
    if scope.mode == "scenarios":
        scenarios = scenario_rows(connection, tenant, policy)
    else:
        records = employee_resources(connection, tenant, scope.employee_code)
        if records is None:
            raise LookupError("Không tìm thấy nhân viên trong phạm vi.")
    with tracing_context(enabled=False):
        state = ASSESSMENT_GRAPH.invoke(
            {
                "run": run_id,
                "observed_at": captured_at,
                "policy": policy,
                "criteria": criteria,
                "employee": records,
                "scenarios": scenarios,
                "findings": [],
                "scores": {},
                "workflow_steps": ["observe"],
            }
        )
    assessment = Assessment(
        id=run_id,
        company_id=tenant,
        policy_version=policy.version,
        scope=scope,
        assessed_at=captured_at,
        findings=state["findings"],
        citations_by_control=assessment_citations(
            connection,
            tenant,
            {control for finding in state["findings"] for control in finding.control_ids},
        ),
        scores=state["scores"],
        workflow_steps=state["workflow_steps"],
    )
    connection.execute(
        text("""
        INSERT INTO app_data.assessments
            (company_id,id,actor_id,request_key,request_hash,policy_version,document)
        VALUES (:tenant,:run,:actor,:key,:hash,:policy,CAST(:doc AS jsonb))
    """),
        params
        | {
            "run": run_id,
            "hash": digest,
            "policy": policy.version,
            "doc": assessment.model_dump_json(),
        },
    )
    return assessment


def load_run(connection: Connection, tenant: UUID, run_id: UUID) -> Assessment | None:
    value = connection.scalar(
        text("""
        SELECT document FROM app_data.assessments WHERE company_id = :tenant AND id = :id
    """),
        {"tenant": tenant, "id": run_id},
    )
    return Assessment.model_validate(value) if value is not None else None
