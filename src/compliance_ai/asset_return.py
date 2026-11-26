from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

from psycopg import Connection
from psycopg.types.json import Jsonb

LOCAL_CALENDAR = timezone(timedelta(hours=7))


def return_due_date(termination: datetime, business_days: int) -> date:
    day = termination.astimezone(LOCAL_CALENDAR).date()
    if business_days == 0:
        return day
    # Start on the first working day strictly after separation.
    day += timedelta(days=1)
    if day.weekday() >= 5:
        day += timedelta(days=7 - day.weekday())
    weeks, extra = divmod(business_days - 1, 5)
    return day + timedelta(days=7 * weeks + extra + (2 if day.weekday() + extra >= 5 else 0))


# Both the assessor and the verifier match the source record to the current inventory row.
RECEIPT_JOIN = """
    LEFT JOIN app_data.asset_return_receipts receipt
      ON (receipt.company_id,receipt.asset_id,receipt.employee_id)=(r.company_id,r.id,r.employee_id)
     AND receipt.ticket_id::text=r.state->>'return_ticket'
     AND receipt.id::text=r.state->>'return_receipt'
"""


def receive_asset(
    connection: Connection, tenant: UUID, employee: str, asset: UUID, ticket: UUID, revision: int
) -> dict:
    row = connection.execute(
        """
        SELECT r.state,r.revision,r.employee_id,a.state,
               (a.plan->>'policy_version')::int = (
                 SELECT max(p.version) FROM app_data.policy_versions p
                 WHERE p.company_id=a.company_id AND p.effective_at<=now())
        FROM app_data.sim_actions a
        JOIN app_data.companies c ON c.id=a.company_id AND c.synthetic
        JOIN app_data.sim_resources r ON (r.company_id,r.id)=(a.company_id,a.target_id)
        JOIN app_data.employees e ON (e.company_id,e.id)=(r.company_id,r.employee_id)
        WHERE a.company_id=%s AND a.id=%s AND r.id=%s AND e.code=%s AND r.kind='asset'
          AND a.plan->>'tool'='request_asset_return' AND a.plan->>'execution_mode'='SIMULATION'
          AND r.state->>'return_ticket'=a.id::text AND e.employment_status='terminated'
          AND e.termination_effective_at<=now() FOR UPDATE OF a,r,e
        """,
        (tenant, ticket, asset, employee),
    ).fetchone()
    if not row:
        raise ValueError("Phiếu, thiết bị hoặc nhân viên không khớp phạm vi bàn giao.")
    state, current_revision, employee_id, action_state, current_policy = row
    existing = connection.execute(
        """
        SELECT id,prior_revision,received_at FROM app_data.asset_return_receipts
        WHERE company_id=%s AND ticket_id=%s
    """,
        (tenant, ticket),
    ).fetchone()
    if existing:
        receipt_id, original_revision, received_at = existing
        if original_revision != revision:
            raise ValueError("Phiếu đã có biên nhận ở phiên bản khác.")
    else:
        if (
            action_state != "WAITING_EXTERNAL"
            or not current_policy
            or current_revision != revision
            or state.get("returned") is not False
            or state.get("return_receipt") is not None
        ):
            raise ValueError("Cần phiếu đang chờ, chính sách và phiên bản tài sản hiện hành.")
        receipt_id = uuid4()
        receipt = connection.execute(
            """
            INSERT INTO app_data.asset_return_receipts
               (company_id,id,ticket_id,asset_id,employee_id,prior_revision)
            VALUES (%s,%s,%s,%s,%s,%s) RETURNING received_at
        """,
            (tenant, receipt_id, ticket, asset, employee_id, revision),
        ).fetchone()
        assert receipt is not None
        received_at = receipt[0]
        connection.execute(
            """
            UPDATE app_data.sim_resources SET state=state || %s,revision=revision+1,updated_at=%s
            WHERE company_id=%s AND id=%s
        """,
            (
                Jsonb(
                    {"returned": True, "return_receipt": str(receipt_id), "custody": "asset_desk"}
                ),
                received_at,
                tenant,
                asset,
            ),
        )
    return {
        "mode": "SIMULATION",
        "source": "synthetic_asset_desk",
        "receipt_id": str(receipt_id),
        "ticket_id": str(ticket),
        "asset_id": str(asset),
        "received_at": received_at.isoformat(),
    }
