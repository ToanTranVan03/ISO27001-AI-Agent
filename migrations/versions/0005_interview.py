"""Allow a signed-in synthetic employee to submit evidence for their own training."""

from alembic import op

revision = "0005_interview"
down_revision = "0004_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE FUNCTION app_auth.own_rubric_threshold(tenant uuid) RETURNS integer
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog
        AS $$
            SELECT (p.document->>'training_min_score')::integer
            FROM app_data.policy_versions p WHERE p.company_id = tenant
                AND p.effective_at <= now() AND EXISTS (
                    SELECT 1 FROM app_auth.memberships m JOIN app_auth.users u ON u.id=m.user_id
                    WHERE m.user_id=app_auth.actor_id() AND m.company_id=tenant
                        AND m.role='employee' AND m.active AND u.enabled
                )
                AND tenant = app_auth.tenant_id()
            ORDER BY p.version DESC LIMIT 1
        $$
    """)
    op.execute("REVOKE EXECUTE ON FUNCTION app_auth.own_rubric_threshold(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION app_auth.own_rubric_threshold(uuid) TO compliance_app")
    scope = """
        company_id = app_auth.tenant_id() AND kind = 'training' AND EXISTS (
            SELECT 1 FROM app_auth.memberships m WHERE m.company_id = sim_resources.company_id
            AND m.employee_id = sim_resources.employee_id AND m.role = 'employee'
        )
    """
    op.execute(f"""
        CREATE POLICY own_training_read ON app_data.sim_resources FOR SELECT TO compliance_app
        USING ({scope})
    """)
    op.execute(f"""
        CREATE POLICY own_training_update ON app_data.sim_resources FOR UPDATE TO compliance_app
        USING ({scope}) WITH CHECK ({scope})
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION app_auth.own_rubric_threshold(uuid)")
    for name in ("own_training_update", "own_training_read"):
        op.execute(f"DROP POLICY {name} ON app_data.sim_resources")
