"""participant profile snapshot

Revision ID: 6dcc94785344
Revises: 696d4d94b1f9
Create Date: 2026-02-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "6dcc94785344"
down_revision: Union[str, Sequence[str], None] = "696d4d94b1f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "participant_progress",
        sa.Column(
            "cumulative_base_effective_score",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
    )

    op.add_column(
        "participants",
        sa.Column("name", sa.String(), nullable=False),
    )

    op.add_column(
        "participants",
        sa.Column("graduation_year", sa.Integer(), nullable=False),
    )

    op.alter_column(
        "participants",
        "user_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_user_challenge",
        "participants",
        ["user_id", "challenge_id"],
    )


def downgrade() -> None:

    op.drop_constraint("uq_user_challenge", "participants", type_="unique")

    op.alter_column(
        "participants",
        "user_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    op.drop_column("participants", "graduation_year")
    op.drop_column("participants", "name")

    op.drop_column(
        "participant_progress",
        "cumulative_base_effective_score",
    )