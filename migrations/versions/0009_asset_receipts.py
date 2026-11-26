"""Independent simulated asset desk receipts."""

from alembic import op

revision = "0009_asset_receipts"
down_revision = "0008_mfa_notice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE app_data.asset_return_receipts (
            company_id uuid NOT NULL, id uuid NOT NULL, ticket_id uuid NOT NULL,
            asset_id uuid NOT NULL, employee_id uuid NOT NULL, prior_revision integer NOT NULL,
            received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (company_id,id), UNIQUE(company_id,ticket_id),
            FOREIGN KEY (company_id,ticket_id) REFERENCES app_data.sim_actions(company_id,id),
            FOREIGN KEY (company_id,asset_id) REFERENCES app_data.sim_resources(company_id,id),
            FOREIGN KEY (company_id,employee_id) REFERENCES app_data.employees(company_id,id)
        )
    """)
    op.execute("ALTER TABLE app_data.asset_return_receipts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app_data.asset_return_receipts FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY receipt_read ON app_data.asset_return_receipts FOR SELECT TO compliance_app
        USING (company_id=app_auth.tenant_id()
               AND app_auth.has_role(company_id,ARRAY['admin','auditor']))
    """)
    op.execute("GRANT SELECT ON app_data.asset_return_receipts TO compliance_app")


def downgrade() -> None:
    op.execute("DROP TABLE app_data.asset_return_receipts")
