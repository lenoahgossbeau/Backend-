"""add status to users

Revision ID: cb0d3cd3d61f
Revises: 0b8fda6de7e5
Create Date: 2026-01-29 14:25:25.821637
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cb0d3cd3d61f'
down_revision: Union[str, Sequence[str], None] = '0b8fda6de7e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='inactive')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'status')
