"""add golden_snapshot to attempts

Revision ID: 90e0a9efb3f9
Revises: db86cc4d6d86
Create Date: 2026-02-24 19:17:13.236240
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "90e0a9efb3f9"
down_revision: Union[str, Sequence[str], None] = "db86cc4d6d86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add golden snapshot column to attempts."""
    op.add_column(
        "attempts",
        sa.Column("golden_snapshot", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Remove golden snapshot column."""
    op.drop_column("attempts", "golden_snapshot")