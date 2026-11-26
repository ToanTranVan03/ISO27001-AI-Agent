from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, computed_field
from sqlalchemy import Connection, text

from compliance_ai.assessments import ScanInput, latest_policy, run_assessment


class AssessmentJob(BaseModel):
    id: UUID
    scope: ScanInput
    policy_version: int
    created_at: datetime
    assessment_id: UUID | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def state(self) -> Literal["PENDING", "COMPLETED"]:
        return "COMPLETED" if self.assessment_id else "PENDING"


def job(connection: Connection, tenant: UUID, identifier: UUID, *, lock=False) -> AssessmentJob:
    query = """
        SELECT id, scope, policy_version, created_at, assessment_id
        FROM app_data.assessment_jobs WHERE company_id=:tenant AND id=:id
    """
    if lock:
        query += " FOR UPDATE"
    row = (
        connection.execute(text(query), {"tenant": tenant, "id": identifier})
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise LookupError("Không tìm thấy yêu cầu đánh giá của bạn.")
    return AssessmentJob.model_validate(dict(row))


def enqueue(
    connection: Connection, tenant: UUID, actor: UUID, scope: ScanInput, key: str
) -> AssessmentJob:
    policy = latest_policy(connection, tenant)
    if policy is None:
        raise LookupError("Chưa có chính sách mô phỏng.")
    params = {"tenant": tenant, "actor": actor, "key": key}
    connection.execute(
        text("""
        INSERT INTO app_data.assessment_jobs
            (company_id,id,actor_id,request_key,scope,policy_version)
        VALUES (:tenant,:id,:actor,:key,CAST(:scope AS jsonb),:version)
        ON CONFLICT (company_id,actor_id,request_key) DO NOTHING
        """),
        params | {"id": uuid4(), "scope": scope.model_dump_json(), "version": policy.version},
    )
    row = (
        connection.execute(
            text("""
        SELECT id,scope,policy_version,created_at,assessment_id
        FROM app_data.assessment_jobs
        WHERE company_id=:tenant AND actor_id=:actor AND request_key=:key
        """),
            params,
        )
        .mappings()
        .one()
    )
    record = AssessmentJob.model_validate(dict(row))
    if record.scope != scope:
        raise ValueError("Khóa yêu cầu đã gắn với phạm vi khác.")
    return record


def resume(connection: Connection, tenant: UUID, actor: UUID, identifier: UUID) -> AssessmentJob:
    record = job(connection, tenant, identifier, lock=True)
    if record.assessment_id:
        return record
    assessment = run_assessment(
        connection,
        tenant,
        actor,
        record.scope,
        f"job/{identifier}",
        expected_policy=record.policy_version,
    )
    connection.execute(
        text("""UPDATE app_data.assessment_jobs SET assessment_id=:run
                WHERE company_id=:tenant AND id=:id"""),
        {"tenant": tenant, "id": identifier, "run": assessment.id},
    )
    return job(connection, tenant, identifier)
