"""Persist synthetic assets, observations and scenario cases."""

from alembic import op

revision = "0002_simulation"
down_revision = "0001_tenant_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE app_data.sim_resources (
            company_id uuid NOT NULL REFERENCES app_data.companies(id),
            id uuid NOT NULL, employee_id uuid NOT NULL,
            kind text NOT NULL CHECK (kind IN ('account','asset','endpoint','training')),
            state jsonb NOT NULL CHECK (jsonb_typeof(state) = 'object'),
            revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
            updated_at timestamptz NOT NULL,
            PRIMARY KEY (company_id, id), UNIQUE (company_id, employee_id, kind),
            FOREIGN KEY (company_id, employee_id) REFERENCES app_data.employees(company_id, id)
        )
    """)
    op.execute("""
        CREATE TABLE app_data.sim_cases (
            company_id uuid NOT NULL REFERENCES app_data.companies(id),
            id uuid NOT NULL, scenario_id text NOT NULL, policy_version integer NOT NULL,
            criterion_id text NOT NULL, observed_at timestamptz NOT NULL,
            evidence jsonb NOT NULL, exclusion_reason text,
            split text NOT NULL CHECK (split IN ('demo','dev','test')),
            PRIMARY KEY (company_id, id),
            FOREIGN KEY (company_id, policy_version)
                REFERENCES app_data.policy_versions(company_id, version)
        )
    """)
    for table in ("sim_resources", "sim_cases"):
        op.execute(f"ALTER TABLE app_data.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE app_data.{table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_read ON app_data.{table} FOR SELECT TO compliance_app
            USING (company_id = app_auth.tenant_id()
                AND app_auth.has_role(company_id, ARRAY['admin','auditor']))
        """)
        op.execute(f"GRANT SELECT ON app_data.{table} TO compliance_app")


def downgrade() -> None:
    op.execute("DROP TABLE app_data.sim_cases")
    op.execute("DROP TABLE app_data.sim_resources")
