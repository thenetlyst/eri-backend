"""sync indexes for attempts and attempt_answers

Revision ID: 4f21bd959457
Revises: e8ad036c129f
Create Date: 2026-03-20 13:27:30.653756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f21bd959457'
down_revision: Union[str, Sequence[str], None] = 'e8ad036c129f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ==========================================================
    # SAFE INDEX SYNC (ALREADY CREATED VIA PSQL)
    # ----------------------------------------------------------
    # These indexes already exist in the DB.
    #
    # This migration:
    # ✔ aligns Alembic with current DB state
    # ✔ ensures future environments create them
    # ✔ avoids duplication via IF NOT EXISTS
    #
    # IMPORTANT:
    # Do NOT use CONCURRENTLY here (Alembic runs in transaction)
    # ==========================================================

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_attempt_status_started
        ON attempts (status, started_at);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_attemptanswer_attempt
        ON attempt_answers (attempt_id);
    """)


def downgrade() -> None:
    """Downgrade schema."""

    # Safe rollback (mainly for dev/testing)
    op.execute("DROP INDEX IF EXISTS idx_attempt_status_started;")
    op.execute("DROP INDEX IF EXISTS idx_attemptanswer_attempt;")