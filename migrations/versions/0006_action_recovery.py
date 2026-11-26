"""Add explicit recovery state for the simulation action ledger."""

from alembic import op

revision = "0006_action_recovery"
down_revision = "0005_interview"
branch_labels = None
depends_on = None

OLD_STATES = (
    "'WAITING_APPROVAL','PROPOSED','APPROVED','REJECTED','EXPIRED','SUCCEEDED',"
    "'WAITING_EXTERNAL','FAILED','VERIFIED','VERIFICATION_FAILED'"
)


def upgrade() -> None:
    op.execute("ALTER TABLE app_data.sim_actions DROP CONSTRAINT sim_actions_state_check")
    op.execute(
        "ALTER TABLE app_data.sim_actions ADD CONSTRAINT sim_actions_state_check "
        f"CHECK (state IN ({OLD_STATES},'ROLLED_BACK'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE app_data.sim_actions DROP CONSTRAINT sim_actions_state_check")
    op.execute("UPDATE app_data.sim_actions SET state='FAILED' WHERE state='ROLLED_BACK'")
    op.execute(
        "ALTER TABLE app_data.sim_actions ADD CONSTRAINT sim_actions_state_check "
        f"CHECK (state IN ({OLD_STATES}))"
    )
