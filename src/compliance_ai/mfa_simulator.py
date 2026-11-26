"""Local operator input for the synthetic identity source."""

from uuid import UUID, uuid4

from psycopg import Connection
from psycopg.types.json import Jsonb


def record_observation(
    connection: Connection,
    tenant: UUID,
    employee: str,
    expected_revision: int,
    registered: bool,
    enforced: bool,
) -> dict:
    row = connection.execute(
        """
        SELECT r.id,r.state,r.revision FROM app_data.sim_resources r
        JOIN app_data.companies c ON c.id=r.company_id AND c.synthetic
        JOIN app_data.employees e ON (e.company_id,e.id)=(r.company_id,r.employee_id)
        WHERE r.company_id=%s AND e.code=%s AND e.employment_status IN ('active','transfer')
          AND r.kind='account' FOR UPDATE OF r,e
        """,
        (tenant, employee),
    ).fetchone()
    if row is None:
        raise ValueError("Không tìm thấy tài khoản nhân viên mô phỏng trong phạm vi.")
    target, state, revision = row
    if (
        revision != expected_revision
        or state.get("protected") is not False
        or state.get("enabled") is not True
    ):
        raise ValueError("Phiên bản hoặc phạm vi tài khoản đã đổi. Hãy đánh giá lại.")
    event = {
        "id": str(uuid4()),
        "source": "synthetic_identity_provider",
        "registered": registered,
        "enforced": enforced,
        "request_id": state.get("mfa_request"),
    }
    connection.execute(
        """UPDATE app_data.sim_resources SET state=state || %s,revision=revision+1,
           updated_at=clock_timestamp() WHERE company_id=%s AND id=%s""",
        (
            Jsonb(
                {"mfa_registered": registered, "mfa_enforced": enforced, "mfa_observation": event}
            ),
            tenant,
            target,
        ),
    )
    return {"mode": "SIMULATION", "employee": employee, "revision": revision + 1, "event": event}
