"""add participant_code to users

Revision ID: 8de95753dbfd
Revises: 4f21bd959457
Create Date: 2026-03-31 14:27:15.738518
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8de95753dbfd'
down_revision: Union[str, Sequence[str], None] = '4f21bd959457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ✅ ADD COLUMN
    op.add_column(
        'users',
        sa.Column('participant_code', sa.String(), nullable=True)
    )

    # ✅ ADD UNIQUE INDEX
    op.create_index(
        op.f('ix_users_participant_code'),
        'users',
        ['participant_code'],
        unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""

    # ✅ REMOVE INDEX
    op.drop_index(op.f('ix_users_participant_code'), table_name='users')

    # ✅ REMOVE COLUMN
    op.drop_column('users', 'participant_code')