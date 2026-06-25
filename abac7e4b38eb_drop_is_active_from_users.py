"""drop is_active from users

Revision ID: abac7e4b38eb
Revises: cb0d3cd3d61f
Create Date: 2026-01-29 14:28:18.750962
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abac7e4b38eb'
down_revision = 'cb0d3cd3d61f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('users', 'is_active')

def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'users',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false')
    )
