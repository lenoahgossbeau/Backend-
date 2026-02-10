"""align users table with cahier de charge

Revision ID: 82402fc6ea39
Revises: abac7e4b38eb
Create Date: 2026-01-29 14:46:39.101099
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '82402fc6ea39'
down_revision = 'abac7e4b38eb'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema."""
    # Renommer hashed_password → password
    op.alter_column('users', 'hashed_password', new_column_name='password')
    # Supprimer username (non prévu dans le cahier de charge)
    op.drop_column('users', 'username')

def downgrade() -> None:
    """Downgrade schema."""
    # Revenir en arrière
    op.alter_column('users', 'password', new_column_name='hashed_password')
    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=False))
