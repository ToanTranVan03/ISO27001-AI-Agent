"""Persist scoped assessment requests until an authenticated caller resumes them."""

from alembic import op

revision = "0010_assessment_jobs"
down_revision = "0009_asset_receipts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE app_data.assessment_jobs (
            company_id uuid NOT NULL,
            id uuid NOT NULL,
            actor_id uuid NOT NULL,
            request_key text NOT NULL,
            scope jsonb NOT NULL,
            policy_version integer NOT NULL,
            assessment_id uuid,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (company_id,id), UNIQUE(company_id,actor_id,request_key),
            FOREIGN KEY (company_id,actor_id) REFERENCES app_auth.memberships(company_id,user_id),
            FOREIGN KEY (company_id,policy_version)
                REFERENCES app_data.policy_versions(company_id,version),
            FOREIGN KEY (company_id,assessment_id) REFERENCES app_data.assessments(company_id,id)
        )
    """)
    op.execute("ALTER TABLE app_data.assessment_jobs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app_data.assessment_jobs FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY assessment_job_owner ON app_data.assessment_jobs TO compliance_app
        USING (company_id=app_auth.tenant_id() AND actor_id=app_auth.actor_id()
               AND app_auth.has_role(company_id,ARRAY['admin','auditor']))
        WITH CHECK (company_id=app_auth.tenant_id() AND actor_id=app_auth.actor_id()
               AND app_auth.has_role(company_id,ARRAY['admin','auditor']))
    """)
    op.execute("GRANT SELECT, INSERT ON app_data.assessment_jobs TO compliance_app")
    op.execute("GRANT UPDATE (assessment_id) ON app_data.assessment_jobs TO compliance_app")


def downgrade() -> None:
    op.execute("DROP TABLE app_data.assessment_jobs")
