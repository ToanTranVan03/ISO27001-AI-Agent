from collections.abc import Iterator
from contextlib import contextmanager
from json import dumps
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import make_url

Role = Literal["admin", "auditor", "employee"]


class Company(BaseModel):
    id: UUID
    name: str
    execution_mode: Literal["SIMULATION"]
    role: Role


class Employee(BaseModel):
    id: UUID
    code: str
    display_name: str
    employment_status: Literal["active", "terminated", "transfer"]
    revision: int


class Document(BaseModel):
    id: UUID
    control_id: str
    source_type: str
    source_ref: str
    content: str


EMPLOYEE_COLUMNS = "id, code, display_name, employment_status, revision"


class Database:
    def __init__(self, url: str) -> None:
        parsed = make_url(url)
        if parsed.drivername != "postgresql+psycopg" or parsed.username != "compliance_app":
            raise ValueError("DATABASE_URL must use the compliance_app PostgreSQL role")
        self.engine = create_engine(
            parsed,
            pool_pre_ping=True,
            hide_parameters=True,
            connect_args={"connect_timeout": 3},
        )

    @contextmanager
    def transaction(
        self, actor: UUID | None = None, tenant: UUID | None = None
    ) -> Iterator[Connection]:
        with self.engine.begin() as connection:
            if actor is not None:
                connection.execute(
                    text("SELECT set_config('app.actor_id', :actor, true)"),
                    {"actor": str(actor)},
                )
            if tenant is not None:
                connection.execute(
                    text("SELECT set_config('app.tenant_id', :tenant, true)"),
                    {"tenant": str(tenant)},
                )
            yield connection

    def ready(self) -> bool:
        with self.transaction() as connection:
            return bool(
                connection.scalar(
                    text("""
                SELECT current_user = 'compliance_app' AND NOT r.rolsuper AND NOT r.rolbypassrls
                    AND NOT has_schema_privilege(current_user, 'benchmark_private', 'USAGE')
                    AND EXISTS (SELECT FROM pg_extension WHERE extname = 'vector')
                    AND row_security_active('app_data.employees')
                FROM pg_roles r WHERE r.rolname = current_user
            """)
                )
            )

    def credentials(self, username: str) -> tuple[UUID, str] | None:
        with self.transaction() as connection:
            row = connection.execute(
                text("SELECT id, password_hash FROM app_auth.credentials(:username)"),
                {"username": username},
            ).one_or_none()
            return (row.id, row.password_hash) if row else None

    def user_enabled(self, actor: UUID) -> bool:
        with self.transaction() as connection:
            return bool(
                connection.scalar(text("SELECT app_auth.user_enabled(:actor)"), {"actor": actor})
            )

    def companies(self, actor: UUID) -> list[Company]:
        with self.transaction(actor) as connection:
            rows = connection.execute(
                text("""
                SELECT c.id, c.name, c.execution_mode, m.role
                FROM app_data.companies c JOIN app_auth.memberships m ON m.company_id = c.id
                ORDER BY c.name, c.id
            """)
            ).mappings()
            return [Company.model_validate(row) for row in rows]

    def membership(self, connection: Connection, tenant: UUID) -> Role | None:
        row = connection.execute(
            text("SELECT role FROM app_auth.memberships WHERE company_id = :tenant"),
            {"tenant": tenant},
        ).one_or_none()
        return row.role if row else None

    def employees(
        self, connection: Connection, tenant: UUID, limit: int, offset: int
    ) -> list[Employee]:
        rows = connection.execute(
            text(
                f"SELECT {EMPLOYEE_COLUMNS} FROM app_data.employees WHERE company_id = :tenant "
                "ORDER BY code LIMIT :limit OFFSET :offset"
            ),
            {"tenant": tenant, "limit": limit, "offset": offset},
        ).mappings()
        return [Employee.model_validate(row) for row in rows]

    def employee(self, connection: Connection, tenant: UUID, target: UUID) -> Employee | None:
        row = (
            connection.execute(
                text(
                    f"SELECT {EMPLOYEE_COLUMNS} FROM app_data.employees "
                    "WHERE company_id = :tenant AND id = :target"
                ),
                {"tenant": tenant, "target": target},
            )
            .mappings()
            .one_or_none()
        )
        return Employee.model_validate(row) if row else None

    def rename_employee(
        self,
        connection: Connection,
        tenant: UUID,
        actor: UUID,
        target: UUID,
        display_name: str,
        expected_revision: int,
    ) -> Employee | None:
        row = (
            connection.execute(
                text(f"""
                UPDATE app_data.employees SET display_name = :display_name,
                    revision = revision + 1, updated_at = now()
                WHERE company_id = :tenant AND id = :target AND revision = :expected_revision
                RETURNING {EMPLOYEE_COLUMNS}
            """),
                {
                    "tenant": tenant,
                    "target": target,
                    "display_name": display_name,
                    "expected_revision": expected_revision,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        connection.execute(
            text("""
                INSERT INTO app_data.audit_events
                    (company_id, id, actor_id, event_type, target_id, detail)
                VALUES (:tenant, :event, :actor, 'employee_renamed', :target,
                    jsonb_build_object('revision', CAST(:new_revision AS integer)))
            """),
            {
                "tenant": tenant,
                "event": uuid4(),
                "actor": actor,
                "target": target,
                "new_revision": row["revision"],
            },
        )
        return Employee.model_validate(row)

    @staticmethod
    def nearest_documents(
        connection: Connection,
        tenant: UUID,
        control_id: str,
        embedding: list[float],
        limit: int,
    ) -> list[Document]:
        if len(embedding) != 384 or not 1 <= limit <= 50:
            raise ValueError("Expected a 384-dimensional embedding and a limit between 1 and 50")
        rows = connection.execute(
            text("""
                SELECT id, control_id, source_type, source_ref, content
                FROM app_data.document_chunks
                WHERE company_id = :tenant AND control_id = :control
                ORDER BY embedding <-> CAST(:embedding AS public.vector), id
                LIMIT :limit
            """),
            {
                "tenant": tenant,
                "control": control_id,
                "embedding": dumps(embedding, allow_nan=False),
                "limit": limit,
            },
        ).mappings()
        return [Document.model_validate(row) for row in rows]
