"""add_profile_details_and_privacy

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-05-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("show_email", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("users", sa.Column("show_created_at", sa.Boolean(), server_default=sa.text("true"), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "show_created_at")
    op.drop_column("users", "show_email")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
