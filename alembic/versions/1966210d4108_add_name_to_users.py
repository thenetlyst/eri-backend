"""add name to users

Revision ID: 1966210d4108
Revises: af669c8a1198
Create Date: 2026-04-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1966210d4108'
down_revision: Union[str, Sequence[str], None] = 'af669c8a1198'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ✅ Add name column (STRICT - NOT NULL)
    op.add_column('users', sa.Column('name', sa.String(), nullable=False))

    # ✅ Allow firebase_uid to be nullable (matches your flow)
    op.alter_column(
        'users',
        'firebase_uid',
        existing_type=sa.VARCHAR(),
        nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""

    # 🔁 Revert firebase_uid constraint
    op.alter_column(
        'users',
        'firebase_uid',
        existing_type=sa.VARCHAR(),
        nullable=False
    )

    # 🔁 Remove name column
    op.drop_column('users', 'name')