"""rename audit_logs to audits

Revision ID: 1a2521e62545
Revises: 
Create Date: 2026-01-29 13:46:27.525462

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1a2521e62545'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('audit_logs', 'audits')


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table('audits', 'audit_logs')
