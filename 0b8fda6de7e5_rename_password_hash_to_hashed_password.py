"""rename password_hash to hashed_password

Revision ID: 0b8fda6de7e5
Revises: 1a2521e62545
Create Date: 2026-01-29 14:18:28.572308
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '0b8fda6de7e5'
down_revision = '1a2521e62545'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')

def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')
