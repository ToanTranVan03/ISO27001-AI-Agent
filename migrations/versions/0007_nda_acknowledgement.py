"""Expose the own-tenant policy version and scoped employee NDA audit append."""

from alembic import op

revision = "0007_nda_acknowledgement"
down_revision = "0006_action_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE FUNCTION app_auth.own_policy_version(tenant uuid) RETURNS integer
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog
        AS $$
            SELECT p.version FROM app_data.policy_versions p
            WHERE p.company_id=tenant AND tenant=app_auth.tenant_id()
                AND p.effective_at<=now() AND EXISTS (
                    SELECT 1 FROM app_auth.memberships m JOIN app_auth.users u ON u.id=m.user_id
                    WHERE m.user_id=app_auth.actor_id() AND m.company_id=tenant
                        AND m.role='employee' AND m.active AND u.enabled
                )
            ORDER BY p.version DESC LIMIT 1
        $$
    """)
    op.execute("REVOKE EXECUTE ON FUNCTION app_auth.own_policy_version(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION app_auth.own_policy_version(uuid) TO compliance_app")
    op.execute("""
        CREATE POLICY own_nda_audit ON app_data.audit_events FOR INSERT TO compliance_app
        WITH CHECK (company_id=app_auth.tenant_id() AND actor_id=app_auth.actor_id()
            AND event_type='NDA_ACKNOWLEDGED' AND EXISTS (
                SELECT 1 FROM app_data.sim_resources r JOIN app_auth.memberships m
                ON (r.company_id,r.employee_id)=(m.company_id,m.employee_id)
                WHERE r.company_id=audit_events.company_id AND r.id=audit_events.target_id
                    AND r.kind='training' AND m.role='employee'
            ))
    """)


def downgrade() -> None:
    op.execute("DROP POLICY own_nda_audit ON app_data.audit_events")
    op.execute("DROP FUNCTION app_auth.own_policy_version(uuid)")
