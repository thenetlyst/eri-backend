"""remove participant_code from participants

Revision ID: af669c8a1198
Revises: 8de95753dbfd
Create Date: 2026-03-31 15:29:27.451768
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af669c8a1198'
down_revision: Union[str, Sequence[str], None] = '8de95753dbfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ✅ Drop UNIQUE constraint first
    op.drop_constraint(
        "uq_participant_code",
        "participants",
        type_="unique"
    )

    # ✅ Drop column
    op.drop_column("participants", "participant_code")


def downgrade() -> None:
    """Downgrade schema."""

    # ✅ Add column back
    op.add_column(
        "participants",
        sa.Column("participant_code", sa.String(), nullable=False)
    )

    # ✅ Restore constraint
    op.create_unique_constraint(
        "uq_participant_code",
        "participants",
        ["participant_code"]
    )