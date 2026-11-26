"""Expose the active employee's pending MFA notice without exposing account state."""

from alembic import op

revision = "0008_mfa_notice"
down_revision = "0007_nda_acknowledgement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE FUNCTION app_auth.own_mfa_notice(tenant uuid) RETURNS uuid
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog
        AS $$
            SELECT a.id FROM app_data.sim_actions a
            JOIN app_data.sim_resources r ON (r.company_id,r.id)=(a.company_id,a.target_id)
            JOIN app_data.employees e ON (e.company_id,e.id)=(r.company_id,r.employee_id)
            JOIN app_auth.memberships m ON (m.company_id,m.employee_id)=(e.company_id,e.id)
            JOIN app_auth.users u ON u.id=m.user_id
            WHERE a.company_id=tenant AND tenant=app_auth.tenant_id()
                AND m.user_id=app_auth.actor_id() AND m.role='employee' AND m.active AND u.enabled
                AND e.employment_status IN ('active','transfer') AND r.kind='account'
                AND r.state @>
                    '{"enabled": true, "protected": false, "mfa_registered": false}'::jsonb
                AND r.state->>'mfa_request'=a.id::text AND a.state='WAITING_EXTERNAL'
                AND a.plan->>'tool'='request_mfa_enrollment'
                AND (a.plan->>'policy_version')::int=app_auth.own_policy_version(tenant)
        $$
    """)
    op.execute("REVOKE EXECUTE ON FUNCTION app_auth.own_mfa_notice(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION app_auth.own_mfa_notice(uuid) TO compliance_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION app_auth.own_mfa_notice(uuid)")
