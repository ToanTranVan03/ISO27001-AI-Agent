"""Tenant identity, initial operational data, vector storage and private oracle."""

from alembic import op

revision = "0001_tenant_foundation"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = (
    "CREATE SCHEMA app_auth",
    "CREATE SCHEMA app_data",
    "CREATE SCHEMA benchmark_private",
    "CREATE EXTENSION IF NOT EXISTS vector",
    "REVOKE CREATE ON SCHEMA public FROM PUBLIC",
    """
    CREATE TABLE app_data.companies (
        id uuid PRIMARY KEY, name text NOT NULL, synthetic boolean NOT NULL CHECK (synthetic),
        execution_mode text NOT NULL DEFAULT 'SIMULATION' CHECK (execution_mode = 'SIMULATION'),
        created_at timestamptz NOT NULL DEFAULT now(), revision integer NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE app_auth.users (
        id uuid PRIMARY KEY, username text NOT NULL UNIQUE CHECK (username = lower(username)),
        password_hash text NOT NULL, enabled boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE app_data.employees (
        company_id uuid NOT NULL REFERENCES app_data.companies(id), id uuid NOT NULL,
        code text NOT NULL, display_name text NOT NULL,
        employment_status text NOT NULL DEFAULT 'active'
            CHECK (employment_status IN ('active', 'terminated', 'transfer')),
        termination_effective_at timestamptz,
        updated_at timestamptz NOT NULL DEFAULT now(), revision integer NOT NULL DEFAULT 1,
        PRIMARY KEY (company_id, id), UNIQUE (company_id, code)
    )
    """,
    """
    CREATE TABLE app_auth.memberships (
        company_id uuid NOT NULL REFERENCES app_data.companies(id),
        user_id uuid NOT NULL REFERENCES app_auth.users(id),
        role text NOT NULL CHECK (role IN ('admin', 'auditor', 'employee')),
        employee_id uuid, active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (company_id, user_id),
        FOREIGN KEY (company_id, employee_id) REFERENCES app_data.employees(company_id, id),
        CHECK ((role = 'employee') = (employee_id IS NOT NULL))
    )
    """,
    """
    CREATE TABLE app_data.policy_versions (
        company_id uuid NOT NULL REFERENCES app_data.companies(id),
        version integer NOT NULL CHECK (version > 0),
        effective_at timestamptz NOT NULL, document jsonb NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (company_id, version)
    )
    """,
    """
    CREATE TABLE app_data.soa_entries (
        company_id uuid NOT NULL, policy_version integer NOT NULL, control_id text NOT NULL,
        applicable boolean NOT NULL, rationale text NOT NULL CHECK (length(trim(rationale)) > 0),
        implementation_state text NOT NULL,
        reviewer_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (company_id, policy_version, control_id),
        FOREIGN KEY (company_id, policy_version)
            REFERENCES app_data.policy_versions(company_id, version),
        FOREIGN KEY (company_id, reviewer_id) REFERENCES app_auth.memberships(company_id, user_id)
    )
    """,
    """
    CREATE TABLE app_data.evidence (
        company_id uuid NOT NULL REFERENCES app_data.companies(id), id uuid NOT NULL,
        source text NOT NULL, source_record_id text NOT NULL, collected_at timestamptz NOT NULL,
        valid_until timestamptz CHECK (valid_until > collected_at),
        evidence_hash text NOT NULL, redacted_payload jsonb NOT NULL,
        execution_mode text NOT NULL CHECK (execution_mode = 'SIMULATION'),
        PRIMARY KEY (company_id, id)
    )
    """,
    """
    CREATE TABLE app_data.document_chunks (
        company_id uuid NOT NULL REFERENCES app_data.companies(id), id uuid NOT NULL,
        control_id text NOT NULL, source_type text NOT NULL, source_ref text NOT NULL,
        content text NOT NULL, embedding public.vector(384) NOT NULL,
        PRIMARY KEY (company_id, id)
    )
    """,
    "CREATE INDEX document_chunk_scope ON app_data.document_chunks (company_id, control_id)",
    """
    CREATE TABLE app_data.audit_events (
        company_id uuid NOT NULL, id uuid NOT NULL, actor_id uuid NOT NULL,
        event_type text NOT NULL, target_id uuid NOT NULL, detail jsonb NOT NULL,
        occurred_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (company_id, id),
        FOREIGN KEY (company_id, actor_id) REFERENCES app_auth.memberships(company_id, user_id)
    )
    """,
    """
    CREATE TABLE benchmark_private.expected_results (
        id uuid PRIMARY KEY, company_id uuid NOT NULL, scenario_id text NOT NULL,
        criterion_id text NOT NULL, target_id uuid NOT NULL, expected_status text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (company_id, scenario_id, criterion_id, target_id)
    )
    """,
)

FUNCTIONS = (
    """
    CREATE FUNCTION app_auth.actor_id() RETURNS uuid
    LANGUAGE sql STABLE SET search_path = pg_catalog
    AS $$ SELECT nullif(current_setting('app.actor_id', true), '')::uuid $$
    """,
    """
    CREATE FUNCTION app_auth.tenant_id() RETURNS uuid
    LANGUAGE sql STABLE SET search_path = pg_catalog
    AS $$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$
    """,
    """
    CREATE FUNCTION app_auth.credentials(login_name text)
    RETURNS TABLE (id uuid, password_hash text)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog
    AS $$
        SELECT u.id, u.password_hash FROM app_auth.users AS u
        WHERE u.username = login_name AND u.enabled
    $$
    """,
    """
    CREATE FUNCTION app_auth.user_enabled(actor uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog
    AS $$ SELECT EXISTS (SELECT FROM app_auth.users WHERE id = actor AND enabled) $$
    """,
    """
    CREATE FUNCTION app_auth.has_role(company uuid, roles text[]) RETURNS boolean
    LANGUAGE sql STABLE SET search_path = pg_catalog
    AS $$
        SELECT EXISTS (
            SELECT FROM app_auth.memberships m
            WHERE m.company_id = company AND m.role = ANY(roles)
        )
    $$
    """,
)

TENANT = "company_id = app_auth.tenant_id()"
READ = f"{TENANT} AND app_auth.has_role(company_id, ARRAY['admin', 'auditor'])"
WRITE = f"{TENANT} AND app_auth.has_role(company_id, ARRAY['admin'])"

POLICIES = (
    (
        "app_auth.memberships",
        "membership_read",
        "SELECT",
        "user_id = app_auth.actor_id() AND active AND app_auth.user_enabled(user_id)",
        None,
    ),
    (
        "app_data.companies",
        "company_read",
        "SELECT",
        "EXISTS (SELECT FROM app_auth.memberships m WHERE m.company_id = companies.id)",
        None,
    ),
    (
        "app_data.employees",
        "employee_read",
        "SELECT",
        f"""{TENANT} AND EXISTS (
            SELECT FROM app_auth.memberships m WHERE m.company_id = employees.company_id
            AND (m.role IN ('admin', 'auditor') OR m.employee_id = employees.id)
        )""",
        None,
    ),
    ("app_data.employees", "employee_edit", "UPDATE", WRITE, WRITE),
    (
        "app_data.audit_events",
        "audit_append",
        "INSERT",
        None,
        f"{WRITE} AND actor_id = app_auth.actor_id()",
    ),
    *(
        (f"app_data.{table}", "tenant_read", "SELECT", READ, None)
        for table in (
            "policy_versions",
            "soa_entries",
            "evidence",
            "document_chunks",
            "audit_events",
        )
    ),
)

GRANTS = (
    "REVOKE ALL ON SCHEMA app_auth, app_data, benchmark_private FROM PUBLIC",
    "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA app_auth FROM PUBLIC",
    "GRANT USAGE ON SCHEMA app_auth, app_data TO compliance_app",
    "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app_auth TO compliance_app",
    "GRANT SELECT ON app_auth.memberships TO compliance_app",
    "GRANT SELECT ON ALL TABLES IN SCHEMA app_data TO compliance_app",
    "GRANT UPDATE (display_name, revision, updated_at) ON app_data.employees TO compliance_app",
    "GRANT INSERT ON app_data.audit_events TO compliance_app",
    "GRANT USAGE ON SCHEMA benchmark_private TO compliance_evaluator",
    "GRANT SELECT ON benchmark_private.expected_results TO compliance_evaluator",
)


def upgrade() -> None:
    for statement in (*SCHEMA, *FUNCTIONS, *GRANTS):
        op.execute(statement)
    for table in sorted({row[0] for row in POLICIES}):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    for table, name, operation, condition, check in POLICIES:
        using = f" USING ({condition})" if condition else ""
        with_check = f" WITH CHECK ({check})" if check else ""
        op.execute(
            f"CREATE POLICY {name} ON {table} FOR {operation} TO compliance_app{using}{with_check}"
        )


def downgrade() -> None:
    op.execute("DROP SCHEMA benchmark_private CASCADE")
    op.execute("DROP SCHEMA app_auth CASCADE")
    op.execute("DROP SCHEMA app_data CASCADE")
    # The shared vector extension and cluster roles survive a database schema rollback.
