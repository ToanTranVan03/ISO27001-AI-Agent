from datetime import UTC, datetime
from hashlib import sha256
from os import getenv
from typing import Annotated, Literal, TypedDict
from unicodedata import combining, normalize
from uuid import UUID, uuid4

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import Connection, text
from sqlalchemy.engine import RowMapping

from compliance_ai.actions import dumps_json
from compliance_ai.assessments import research_catalog
from compliance_ai.nda import NdaAcknowledgement, NdaReceipt, acknowledged, scoped_request
from compliance_ai.semantic import semantic_evidence

Kind = Literal["initial", "retest"]
Response = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=2000)]
PHRASES = {
    "recognize": ("dang ngo", "gia mao", "lua dao", "bat thuong", "phishing"),
    "safe_response": ("khong bam", "khong nhap", "khong mo", "khong truy cap", "khong tra loi"),
    "report": ("bao cao", "thong bao", "bao cho", "lien he", "gui cho"),
}
CHANNELS = ("soc", "helpdesk", "an toan thong tin", "bao mat", "kenh noi bo")
FOLLOWUP = {
    "recognize": "Dấu hiệu nào khiến bạn nghi ngờ yêu cầu đó?",
    "safe_response": "Bạn sẽ tránh thực hiện thao tác nào với nội dung đó?",
    "report": "Bạn sẽ báo cáo cho ai hoặc qua kênh nội bộ nào?",
}


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Kind
    answer: Response
    use_local_model: bool = False


class Grade(BaseModel):
    status: Literal["FOLLOWUP", "PASSED", "FAILED", "HUMAN_REVIEW"]
    score: int = Field(ge=0, le=100)
    criteria_met: list[str]
    followup: str | None = None
    evaluator: Literal["DETERMINISTIC_RUBRIC", "OLLAMA_LOCAL"] = "DETERMINISTIC_RUBRIC"
    model: str | None = None


class InterviewState(TypedDict, total=False):
    answer: str
    previous: list[str]
    followups: int
    threshold: int
    model: str
    grade: dict[str, object]


def plain(value: str) -> str:
    return "".join(
        ch for ch in normalize("NFD", value.casefold().replace("đ", "d")) if not combining(ch)
    )


def assess_text(state: InterviewState) -> InterviewState:
    message = plain(state["answer"])
    words = message.split()
    suspicious = any(
        marker in message
        for marker in (
            "ignore previous",
            "system prompt",
            "bo qua chi thi",
            "cho diem toi da",
            "dung rubric",
        )
    )
    recognized = {key for key, terms in PHRASES.items() if any(term in message for term in terms)}
    if not any(channel in words or channel in message for channel in CHANNELS):
        recognized.discard("report")
    if any(term in message for term in ("khong bao cao", "khong thong bao", "khong lien he")):
        recognized.discard("report")
    model = state.get("model")
    proof = semantic_evidence(model, state["answer"]) if model and not suspicious else None
    if proof:
        recognized, _ = proof
    if suspicious or (model and proof is None):
        grade = Grade(status="HUMAN_REVIEW", score=0, criteria_met=[])
    else:
        recognized.update(state.get("previous", []))
        rubric = research_catalog().interview
        points = sum(item.weight for item in rubric.criteria if item.id in recognized)
        unmet = next((key for key in FOLLOWUP if key not in recognized), None)
        if points >= state["threshold"] and "report" in recognized:
            grade = Grade(status="PASSED", score=points, criteria_met=sorted(recognized))
        elif state.get("followups", 0) == 0 and unmet:
            grade = Grade(
                status="FOLLOWUP",
                score=points,
                criteria_met=sorted(recognized),
                followup=FOLLOWUP[unmet],
            )
        else:
            grade = Grade(status="FAILED", score=points, criteria_met=sorted(recognized))
    if model and not suspicious:
        grade = grade.model_copy(update={"evaluator": "OLLAMA_LOCAL", "model": model})
    return {"grade": grade.model_dump()}


builder = StateGraph(InterviewState)
builder.add_node("score_rubric", assess_text)
builder.add_edge(START, "score_rubric")
builder.add_edge("score_rubric", END)
GRAPH = builder.compile()


def own_training(connection: Connection, tenant: UUID, *, lock=False) -> RowMapping:
    query = """
        SELECT r.id,r.state,r.revision FROM app_data.sim_resources r
        JOIN app_auth.memberships m
        ON (r.company_id,r.employee_id)=(m.company_id,m.employee_id)
        WHERE r.company_id=:tenant AND r.kind='training' AND m.role='employee'
    """
    if lock:
        query += " FOR UPDATE OF r"
    row = connection.execute(text(query), {"tenant": tenant}).mappings().one_or_none()
    if row is None:
        raise LookupError("Không tìm thấy hồ sơ đào tạo của bạn.")
    return row


def training_view(connection: Connection, tenant: UUID) -> dict[str, object]:
    row = own_training(connection, tenant)
    state = row["state"]
    version = connection.scalar(text("SELECT app_auth.own_policy_version(:t)"), {"t": tenant})
    nda = scoped_request(state, tenant, row["id"], version) if version is not None else None
    rubric = research_catalog().interview
    return {
        "initial_question": rubric.initial,
        "retest_question": rubric.retest,
        "initial": state.get("initial"),
        "retest": state.get("retest"),
        "assignment": state.get("assignment"),
        "nda": nda.model_dump(mode="json") if nda else None,
        "mfa_request_id": connection.scalar(
            text("SELECT app_auth.own_mfa_notice(:t)"), {"t": tenant}
        ),
        "revision": row["revision"],
        "local_model_available": bool(getenv("LOCAL_INTERVIEW_MODEL")),
        "mode": "SIMULATION",
    }


def update(
    connection: Connection,
    tenant: UUID,
    row: RowMapping,
    state: dict[str, object],
) -> None:
    connection.execute(
        text("""
        UPDATE app_data.sim_resources SET state=CAST(:doc AS jsonb),
            revision=revision+1,updated_at=now() WHERE company_id=:tenant AND id=:target
    """),
        {"tenant": tenant, "target": row["id"], "doc": dumps_json(state)},
    )


def acknowledge_nda(
    connection: Connection, tenant: UUID, actor: UUID, payload: NdaAcknowledgement
) -> NdaReceipt:
    row = own_training(connection, tenant, lock=True)
    state = dict(row["state"])
    version = connection.scalar(text("SELECT app_auth.own_policy_version(:t)"), {"t": tenant})
    request = scoped_request(state, tenant, row["id"], version) if version is not None else None
    if not request or request.id != payload.request_id:
        raise LookupError("Không tìm thấy yêu cầu NDA hiện hành của bạn.")
    if not payload.acknowledged or payload.document_hash != request.document.sha256:
        raise ValueError("Cần xác nhận đúng nội dung cam kết.")
    if acknowledged(request) and request.receipt and request.receipt.submitted_by == actor:
        return request.receipt
    if request.status != "ASSIGNED" or payload.expected_revision != row["revision"]:
        raise ValueError("Hồ sơ đã đổi. Hãy mở lại yêu cầu.")
    receipt = NdaReceipt(
        request_id=request.id,
        document_hash=request.document.sha256,
        submitted_by=actor,
        submitted_at=datetime.now(UTC),
        evidence_id=uuid4(),
    )
    request.receipt = receipt
    request.status = "ACKNOWLEDGED"
    state.update(nda_request=request.model_dump(mode="json"), nda_signed=True)
    update(connection, tenant, row, state)
    connection.execute(
        text("""
        INSERT INTO app_data.audit_events(company_id,id,actor_id,event_type,target_id,detail)
        VALUES (:t,:id,:actor,'NDA_ACKNOWLEDGED',:target,CAST(:detail AS jsonb))
    """),
        {
            "t": tenant,
            "id": receipt.evidence_id,
            "actor": actor,
            "target": row["id"],
            "detail": dumps_json(
                {"request_id": str(request.id), "document_hash": receipt.document_hash}
            ),
        },
    )
    return receipt


def complete(connection: Connection, tenant: UUID, actor: UUID) -> dict[str, object]:
    row = own_training(connection, tenant, lock=True)
    state = dict(row["state"])
    assignment = state.get("assignment")
    if not assignment:
        raise ValueError("Chưa có bài học được giao.")
    if assignment["status"] == "ASSIGNED":
        assignment.update(
            status="COMPLETED",
            completed_by=str(actor),
            completed_at=datetime.now(UTC).isoformat(),
            evidence_id=str(uuid4()),
            source="synthetic_employee_submission",
        )
        state["assignment"] = assignment
        update(connection, tenant, row, state)
    return assignment


def answer(
    connection: Connection,
    tenant: UUID,
    actor: UUID,
    submission: Answer,
) -> dict[str, object]:
    row = own_training(connection, tenant, lock=True)
    state = dict(row["state"])
    if submission.kind == "retest" and (state.get("assignment") or {}).get("status") != "COMPLETED":
        raise ValueError("Hãy xác nhận hoàn thành bài học trước khi kiểm tra lại.")
    history = state.get(submission.kind) or {}
    if history and history["grade"]["status"] != "FOLLOWUP":
        raise ValueError("Lượt phỏng vấn này đã kết thúc.")
    threshold = connection.scalar(
        text("""
        SELECT (document->>'training_min_score')::integer FROM app_data.policy_versions
        WHERE company_id=:tenant AND effective_at <= now() ORDER BY version DESC LIMIT 1
    """),
        {"tenant": tenant},
    )
    # Employees do not have direct access to policy rows.
    if threshold is None:
        threshold = connection.scalar(
            text("SELECT app_auth.own_rubric_threshold(:tenant)"), {"tenant": tenant}
        )
    if threshold is None:
        raise ValueError("Thiếu phiên bản chính sách đào tạo.")
    model = getenv("LOCAL_INTERVIEW_MODEL") if submission.use_local_model else None
    if submission.use_local_model and not model:
        raise ValueError("Chưa cấu hình Ollama cho bài phỏng vấn mô phỏng.")
    with tracing_context(enabled=False):
        output = GRAPH.invoke(
            {
                "answer": submission.answer,
                "previous": (history.get("grade") or {}).get("criteria_met", []),
                "followups": 1 if history else 0,
                "threshold": threshold,
                **({"model": model} if model else {}),
            }
        )
    grade = Grade.model_validate(output["grade"])
    observation: dict[str, object] = {
        "grade": grade.model_dump(),
        "submitted_by": str(actor),
        "evidence_id": str(uuid4()),
        "answer_sha256": sha256(submission.answer.encode()).hexdigest(),
        "observed_at": datetime.now(UTC).isoformat(),
        "source": "synthetic_employee_submission",
    }
    if history:
        observation["first_attempt"] = history
    state[submission.kind] = observation
    if submission.kind == "retest" and grade.status == "PASSED":
        state["passed_retest"] = True
    update(connection, tenant, row, state)
    return observation
