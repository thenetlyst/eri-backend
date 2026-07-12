"""attempt progress fields

Revision ID: db86cc4d6d86
Revises: 6dcc94785344
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "db86cc4d6d86"
down_revision: Union[str, Sequence[str], None] = "6dcc94785344"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------
    # Attempt Events table (event sourcing base)
    # -------------------------------------------------
    op.create_table(
        "attempt_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("client_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
    )

    # -------------------------------------------------
    # attempts.progress_applied  ⭐ FIXED
    # -------------------------------------------------
    op.add_column(
        "attempts",
        sa.Column(
            "progress_applied",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # -------------------------------------------------
    # participant_progress timestamps
    # -------------------------------------------------
    op.add_column(
        "participant_progress",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )

    op.add_column(
        "participant_progress",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )

    # -------------------------------------------------
    # graduation_year → string
    # -------------------------------------------------
    op.alter_column(
        "participants",
        "graduation_year",
        existing_type=sa.INTEGER(),
        type_=sa.String(),
        existing_nullable=False,
    )

    # -------------------------------------------------
    # questions.content_json (images + rich content)
    # -------------------------------------------------
    op.add_column(
        "questions",
        sa.Column(
            "content_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("questions", "content_json")

    op.alter_column(
        "participants",
        "graduation_year",
        existing_type=sa.String(),
        type_=sa.INTEGER(),
        existing_nullable=False,
    )

    op.drop_column("participant_progress", "updated_at")
    op.drop_column("participant_progress", "created_at")
    op.drop_column("attempts", "progress_applied")

    op.drop_table("attempt_events")