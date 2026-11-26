"""Persist immutable assessment runs and expose their policy-scoped input."""

from alembic import op

revision = "0003_assessments"
down_revision = "0002_simulation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE app_data.assessments (
            company_id uuid NOT NULL, id uuid NOT NULL, actor_id uuid NOT NULL,
            request_key text NOT NULL, request_hash text NOT NULL,
            policy_version integer NOT NULL, document jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (company_id, id), UNIQUE (company_id, actor_id, request_key),
            FOREIGN KEY (company_id, actor_id) REFERENCES app_auth.memberships(company_id,user_id),
            FOREIGN KEY (company_id, policy_version)
                REFERENCES app_data.policy_versions(company_id,version)
        )
    """)
    op.execute("ALTER TABLE app_data.assessments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app_data.assessments FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY assessment_read ON app_data.assessments FOR SELECT TO compliance_app
        USING (company_id = app_auth.tenant_id()
            AND app_auth.has_role(company_id, ARRAY['admin','auditor']))
    """)
    op.execute("""
        CREATE POLICY assessment_create ON app_data.assessments FOR INSERT TO compliance_app
        WITH CHECK (company_id = app_auth.tenant_id() AND actor_id = app_auth.actor_id()
            AND app_auth.has_role(company_id, ARRAY['admin','auditor']))
    """)
    op.execute("GRANT SELECT, INSERT ON app_data.assessments TO compliance_app")


def downgrade() -> None:
    op.execute("DROP TABLE app_data.assessments")
