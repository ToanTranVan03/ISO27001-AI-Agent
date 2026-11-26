"""Tenant-scoped simulation action ledger and fixed resource updates."""

from alembic import op

revision = "0004_actions"
down_revision = "0003_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE app_data.sim_actions (
            company_id uuid NOT NULL, id uuid NOT NULL, run_id uuid NOT NULL,
            finding_id uuid NOT NULL, target_id uuid NOT NULL, requested_by uuid NOT NULL,
            plan jsonb NOT NULL, plan_hash text NOT NULL, state text NOT NULL,
            approved_by uuid, approval_expires_at timestamptz, executed_at timestamptz,
            execution_key text, result jsonb, verification jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (company_id,id), UNIQUE(company_id,run_id,finding_id),
            UNIQUE(company_id,execution_key),
            FOREIGN KEY (company_id,run_id) REFERENCES app_data.assessments(company_id,id),
            FOREIGN KEY (company_id,target_id) REFERENCES app_data.sim_resources(company_id,id),
            FOREIGN KEY (company_id,requested_by)
                REFERENCES app_auth.memberships(company_id,user_id),
            FOREIGN KEY (company_id,approved_by)
                REFERENCES app_auth.memberships(company_id,user_id),
            CHECK (approved_by IS NULL OR approved_by <> requested_by),
            CHECK (state IN ('WAITING_APPROVAL','PROPOSED','APPROVED','REJECTED','EXPIRED',
                'SUCCEEDED','WAITING_EXTERNAL','FAILED','VERIFIED','VERIFICATION_FAILED'))
        )
    """)
    for command in ("ENABLE", "FORCE"):
        op.execute(f"ALTER TABLE app_data.sim_actions {command} ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY action_read ON app_data.sim_actions FOR SELECT TO compliance_app
        USING (company_id = app_auth.tenant_id()
            AND app_auth.has_role(company_id, ARRAY['admin','auditor']))
    """)
    op.execute("""
        CREATE POLICY action_insert ON app_data.sim_actions FOR INSERT TO compliance_app
        WITH CHECK (company_id = app_auth.tenant_id() AND requested_by = app_auth.actor_id()
            AND app_auth.has_role(company_id, ARRAY['admin','auditor']))
    """)
    for table in ("sim_actions", "sim_resources"):
        op.execute(f"""
            CREATE POLICY admin_update ON app_data.{table} FOR UPDATE TO compliance_app
            USING (company_id = app_auth.tenant_id()
                AND app_auth.has_role(company_id,ARRAY['admin']))
            WITH CHECK (company_id = app_auth.tenant_id()
                AND app_auth.has_role(company_id,ARRAY['admin']))
        """)
    op.execute("GRANT SELECT, INSERT ON app_data.sim_actions TO compliance_app")
    op.execute("""
        GRANT UPDATE (state, approved_by, approval_expires_at, executed_at, execution_key,
            result, verification) ON app_data.sim_actions TO compliance_app
    """)
    op.execute(
        "GRANT UPDATE (state, revision, updated_at) ON app_data.sim_resources TO compliance_app"
    )


def downgrade() -> None:
    op.execute(
        "REVOKE UPDATE (state, revision, updated_at) ON app_data.sim_resources FROM compliance_app"
    )
    op.execute("DROP POLICY admin_update ON app_data.sim_resources")
    op.execute("DROP TABLE app_data.sim_actions")
