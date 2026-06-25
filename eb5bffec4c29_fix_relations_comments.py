"""fix relations comments

Revision ID: eb5bffec4c29
Revises: 30b13eb432d8
Create Date: 2026-02-06 16:03:58.153250
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "eb5bffec4c29"
down_revision: Union[str, Sequence[str], None] = "30b13eb432d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # academic_careers
    op.add_column(
        "academic_careers",
        sa.Column("profile_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        None,
        "academic_careers",
        "profiles",
        ["profile_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # comments
    op.add_column("comments", sa.Column("content", sa.Text(), nullable=False))
    op.add_column("comments", sa.Column("user_id", sa.Integer(), nullable=False))
    op.add_column("comments", sa.Column("project_id", sa.Integer(), nullable=True))
    op.add_column("comments", sa.Column("publication_id", sa.Integer(), nullable=True))

    op.alter_column(
        "comments",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    op.create_foreign_key(
        None, "comments", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        None, "comments", "projects", ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        None,
        "comments",
        "publications",
        ["publication_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_column("comments", "comment")
    op.drop_column("comments", "project")


def downgrade() -> None:
    """Downgrade schema."""

    # comments
    op.add_column(
        "comments",
        sa.Column("project", sa.VARCHAR(length=100), nullable=False),
    )
    op.add_column(
        "comments",
        sa.Column("comment", sa.TEXT(), nullable=False),
    )

    op.drop_constraint(None, "comments", type_="foreignkey")
    op.drop_constraint(None, "comments", type_="foreignkey")
    op.drop_constraint(None, "comments", type_="foreignkey")

    op.alter_column(
        "comments",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )

    op.drop_column("comments", "publication_id")
    op.drop_column("comments", "project_id")
    op.drop_column("comments", "user_id")
    op.drop_column("comments", "content")

    # academic_careers
    op.drop_constraint(None, "academic_careers", type_="foreignkey")
    op.drop_column("academic_careers", "profile_id")
