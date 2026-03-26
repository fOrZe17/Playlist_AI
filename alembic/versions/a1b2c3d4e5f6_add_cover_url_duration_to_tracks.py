"""add_cover_url_duration_to_tracks

Revision ID: a1b2c3d4e5f6
Revises: 43f21411eb2e
Create Date: 2026-03-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '43f21411eb2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tracks', sa.Column('cover_url', sa.String(length=500), nullable=True))
    op.add_column('tracks', sa.Column('duration', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tracks', 'duration')
    op.drop_column('tracks', 'cover_url')
