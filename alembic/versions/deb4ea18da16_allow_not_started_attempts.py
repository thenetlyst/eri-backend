"""allow_not_started_attempts

Revision ID: deb4ea18da16
Revises: 1966210d4108
Create Date: 2026-07-22 21:12:35.678709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "deb4ea18da16"
down_revision: Union[str, Sequence[str], None] = "1966210d4108"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "attempts",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "attempts",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )