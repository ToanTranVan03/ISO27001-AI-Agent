from csv import writer
from hashlib import sha256
from io import StringIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Response
from sqlalchemy import Connection, text

from compliance_ai.actions import (
    Action,
    Decision,
    Preview,
    Proof,
    decide,
    execute,
    find_action,
    plan_action,
    preview_action,
    rollback,
    show,
    verify,
)
from compliance_ai.assessments import (
    Assessment,
    ScanInput,
    load_run,
    research_catalog,
    run_assessment,
)
from compliance_ai.db import Document
from compliance_ai.interview import Answer, acknowledge_nda, answer, complete, training_view
from compliance_ai.nda import NdaAcknowledgement, NdaReceipt
from compliance_ai.rag import retrieve
from compliance_ai.tenant_api import DB, Actor, Database

router = APIRouter(prefix="/api/v1/companies/{company_id}")
RetryKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=100)]


@router.get("/knowledge/{control_id}/chunks/{chunk_id}", tags=["knowledge"])
def cited_chunk(
    company_id: UUID,
    control_id: str,
    chunk_id: UUID,
    actor: Actor,
    db: DB,
    expected_sha256: Annotated[str, Query(pattern=r"^[0-9a-f]{64}$")],
) -> Document:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        row = (
            connection.execute(
                text("""
            SELECT id,control_id,source_type,source_ref,content FROM app_data.document_chunks
            WHERE company_id=:tenant AND control_id=:control AND id=:chunk
        """),
                {"tenant": company_id, "control": control_id, "chunk": chunk_id},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise HTTPException(404, "Không tìm thấy đoạn tài liệu trong phạm vi.")
        doc = Document.model_validate(dict(row))
        if sha256(doc.content.encode()).hexdigest() != expected_sha256:
            raise HTTPException(409, "Nội dung hiện tại khác phiên bản đã dẫn.")
        return doc


def authorize(db: Database, connection: Connection, company_id: UUID, *, admin=False) -> None:
    role = db.membership(connection, company_id)
    if role is None:
        raise HTTPException(404, "Không tìm thấy doanh nghiệp.")
    if role not in ("admin", "auditor") or (admin and role != "admin"):
        raise HTTPException(403, "Vai trò hiện tại không có quyền thao tác.")


@router.post("/assessments", tags=["assessments"])
def scan(company_id: UUID, payload: ScanInput, actor: Actor, db: DB, key: RetryKey) -> Assessment:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        try:
            return run_assessment(connection, company_id, actor, payload, key)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        except LookupError as error:
            raise HTTPException(404, str(error)) from error


@router.get("/assessments/{run_id}", tags=["assessments"])
def assessment(company_id: UUID, run_id: UUID, actor: Actor, db: DB) -> Assessment:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        result = load_run(connection, company_id, run_id)
        if result is None:
            raise HTTPException(404, "Không tìm thấy đánh giá.")
        return result


@router.get("/assessments/{run_id}/reports/gap", tags=["reports"])
def gap_report(company_id: UUID, run_id: UUID, actor: Actor, db: DB) -> dict[str, object]:
    record = assessment(company_id, run_id, actor, db)
    return {
        "report_type": "gap",
        "title": "Báo cáo khoảng cách",
        "mode": record.execution_mode,
        "assessment": record.model_dump(mode="json"),
    }


@router.post("/assessments/{run_id}/findings/{finding_id}/plan", tags=["actions"])
def create_plan(
    company_id: UUID,
    run_id: UUID,
    finding_id: UUID,
    actor: Actor,
    db: DB,
) -> Action:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        try:
            return plan_action(connection, company_id, actor, run_id, finding_id)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.get("/actions/{action_id}", tags=["actions"])
def get_plan(company_id: UUID, action_id: UUID, actor: Actor, db: DB) -> Action:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        try:
            return show(find_action(connection, company_id, action_id))
        except LookupError as error:
            raise HTTPException(404, str(error)) from error


@router.post("/actions/{action_id}/decision", tags=["actions"])
def action_decision(
    company_id: UUID,
    action_id: UUID,
    payload: Decision,
    actor: Actor,
    db: DB,
) -> Action:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id, admin=True)
        try:
            return decide(connection, company_id, actor, action_id, payload)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.post("/actions/{action_id}/dry-run", tags=["actions"])
def dry_run_action(
    company_id: UUID, action_id: UUID, payload: Proof, actor: Actor, db: DB
) -> Preview:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        try:
            return preview_action(connection, company_id, action_id, payload)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.post("/actions/{action_id}/execute", tags=["actions"])
def execute_action(
    company_id: UUID,
    action_id: UUID,
    payload: Proof,
    actor: Actor,
    db: DB,
    key: RetryKey,
) -> Action:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id, admin=True)
        try:
            return execute(connection, company_id, actor, action_id, payload, key)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.post("/actions/{action_id}/verify", tags=["actions"])
def verify_action(company_id: UUID, action_id: UUID, actor: Actor, db: DB) -> Action:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id, admin=True)
        try:
            return verify(connection, company_id, actor, action_id)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.get("/assessments/{run_id}/reports/remediation", tags=["reports"])
def remediation_report(company_id: UUID, run_id: UUID, actor: Actor, db: DB) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        record = load_run(connection, company_id, run_id)
        if record is None:
            raise HTTPException(404, "Không tìm thấy đánh giá.")
        rows = connection.execute(
            text("""
            SELECT * FROM app_data.sim_actions WHERE company_id=:tenant AND run_id=:run
            ORDER BY created_at,id
        """),
            {"tenant": company_id, "run": run_id},
        ).mappings()
        return {
            "report_type": "remediation",
            "title": "Báo cáo khắc phục",
            "mode": record.execution_mode,
            "assessment_id": str(run_id),
            "policy_version": record.policy_version,
            "actions": [show(row).model_dump(mode="json") for row in rows],
        }


@router.get("/reports/audit", tags=["reports"])
def audit_report(company_id: UUID, actor: Actor, db: DB) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        rows = connection.execute(
            text("""
            SELECT id,actor_id,event_type,target_id,occurred_at FROM app_data.audit_events
            WHERE company_id=:tenant ORDER BY occurred_at DESC LIMIT 100
        """),
            {"tenant": company_id},
        ).mappings()
        return {
            "report_type": "audit",
            "title": "Nhật ký",
            "mode": "SIMULATION",
            "events": [dict(row) for row in rows],
        }


@router.get("/me/training", tags=["training"])
def get_training(company_id: UUID, actor: Actor, db: DB) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        try:
            return training_view(connection, company_id)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error


@router.post("/me/training/complete", tags=["training"])
def complete_training(company_id: UUID, actor: Actor, db: DB) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        try:
            return complete(connection, company_id, actor)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.post("/me/nda/acknowledge", tags=["training"])
def submit_nda(company_id: UUID, payload: NdaAcknowledgement, actor: Actor, db: DB) -> NdaReceipt:
    with db.transaction(actor, company_id) as connection:
        try:
            return acknowledge_nda(connection, company_id, actor, payload)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.post("/me/interview", tags=["training"])
def submit_interview(company_id: UUID, payload: Answer, actor: Actor, db: DB) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        try:
            return answer(connection, company_id, actor, payload)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error


@router.get("/reports/soa", tags=["reports"])
def soa_report(company_id: UUID, actor: Actor, db: DB) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        policy_version = connection.scalar(
            text("""
            SELECT version FROM app_data.policy_versions
            WHERE company_id=:tenant AND effective_at<=now() ORDER BY version DESC LIMIT 1
        """),
            {"tenant": company_id},
        )
        rows = connection.execute(
            text("""
            SELECT control_id,applicable,rationale,implementation_state,reviewer_id
            FROM app_data.soa_entries WHERE company_id=:tenant AND policy_version=:policy
            ORDER BY control_id
        """),
            {"tenant": company_id, "policy": policy_version},
        ).mappings()
        entries = [dict(row) for row in rows]
        return {
            "report_type": "soa_extract",
            "title": "Bản trích SoA",
            "mode": "SIMULATION",
            "approval_state": "DRAFT" if entries else "NO_REVIEWED_ENTRIES",
            "policy_version": policy_version,
            "entries": entries,
        }


@router.get("/knowledge/{control_id}", tags=["knowledge"])
def knowledge(
    company_id: UUID,
    control_id: str,
    actor: Actor,
    db: DB,
    query: Annotated[str, Query(min_length=1, max_length=500)],
) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        references = [item for item in research_catalog().controls if item.id == control_id]
        if not references:
            raise HTTPException(404, "Không tìm thấy mã tham chiếu.")
        documents = retrieve(db, connection, company_id, control_id, query)
        return {
            "source_mode": "tenant_knowledge" if documents else "research_rubric",
            "reference": references[0].model_dump(),
            "documents": [item.model_dump(mode="json") for item in documents],
        }


@router.get("/assessments/{run_id}/reports/gap.csv", tags=["reports"])
def export_gap(company_id: UUID, run_id: UUID, actor: Actor, db: DB) -> Response:
    record = assessment(company_id, run_id, actor, db)
    buffer = StringIO(newline="")
    output = writer(buffer)
    output.writerow(["run_id", "policy_version", "criterion", "controls", "status", "evidence_ids"])
    for item in record.findings:
        output.writerow(
            [
                str(record.id),
                record.policy_version,
                item.criterion_id,
                " ".join(item.control_ids),
                item.status,
                " ".join(item.evidence_ids),
            ]
        )
    return Response(
        "\ufeff" + buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="gap-{run_id}.csv"'},
    )


@router.get("/assessments/{run_id}/compare", tags=["reports"])
def compare(
    company_id: UUID,
    run_id: UUID,
    before: UUID,
    actor: Actor,
    db: DB,
) -> dict[str, object]:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id)
        newer = load_run(connection, company_id, run_id)
        older = load_run(connection, company_id, before)
        if newer is None or older is None:
            raise HTTPException(404, "Không tìm thấy đánh giá.")
        if (
            newer.policy_version != older.policy_version
            or newer.scope != older.scope
            or newer.assessed_at < older.assessed_at
        ):
            raise HTTPException(409, "Chỉ so sánh cùng phạm vi và phiên bản theo thứ tự thời gian.")
        previous = {(item.criterion_id, item.target_id): item.status for item in older.findings}
        current = {(item.criterion_id, item.target_id): item.status for item in newer.findings}
        if previous.keys() != current.keys():
            raise HTTPException(409, "Danh sách đối tượng đã thay đổi.")
        return {
            "before": older.id,
            "after": newer.id,
            "policy_version": newer.policy_version,
            "before_scores": older.scores,
            "after_scores": newer.scores,
            "changes": [
                {"criterion": criterion, "target": target, "before": old, "after": current[key]}
                for key, old in previous.items()
                for criterion, target in [key]
                if old != current[key]
            ],
        }


@router.post("/actions/{action_id}/rollback", tags=["actions"])
def rollback_action(
    company_id: UUID, action_id: UUID, payload: Proof, actor: Actor, db: DB
) -> Action:
    with db.transaction(actor, company_id) as connection:
        authorize(db, connection, company_id, admin=True)
        try:
            return rollback(connection, company_id, actor, action_id, payload)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
