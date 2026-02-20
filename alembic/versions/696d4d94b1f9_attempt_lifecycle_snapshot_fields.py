"""attempt lifecycle snapshot fields

Revision ID: 696d4d94b1f9
Revises: e28d11afa123
Create Date: 2026-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "696d4d94b1f9"
down_revision: Union[str, Sequence[str], None] = "e28d11afa123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ---- Attempt navigation ----
    op.add_column(
        "attempts",
        sa.Column("current_index", sa.Integer(), nullable=False, server_default="0"),
    )

    op.add_column(
        "attempts",
        sa.Column("last_resumed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ---- AttemptAnswer hint replay + navigation ----
    op.add_column(
        "attempt_answers",
        sa.Column("first_hint_opened_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "attempt_answers",
        sa.Column("hint_open_count", sa.Integer(), nullable=False, server_default="0"),
    )

    op.add_column(
        "attempt_answers",
        sa.Column("time_to_first_hint_seconds", sa.Integer(), nullable=True),
    )

    op.add_column(
        "attempt_answers",
        sa.Column("visited_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "attempt_answers",
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "attempt_answers",
        sa.Column("marked_for_review", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("attempt_answers", "marked_for_review")
    op.drop_column("attempt_answers", "last_viewed_at")
    op.drop_column("attempt_answers", "visited_at")
    op.drop_column("attempt_answers", "time_to_first_hint_seconds")
    op.drop_column("attempt_answers", "hint_open_count")
    op.drop_column("attempt_answers", "first_hint_opened_at")

    op.drop_column("attempts", "last_resumed_at")
    op.drop_column("attempts", "current_index")