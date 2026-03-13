"""remove milliseconds from created_at

Revision ID: 28ee643b3551
Revises: c4d28569ec55
Create Date: 2026-03-12 23:58:13.850254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28ee643b3551'
down_revision: Union[str, Sequence[str], None] = 'c4d28569ec55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Изменяем server_default на date_trunc без миллисекунд
    op.alter_column('users', 'created_at',
                    server_default=sa.text("date_trunc('second', now())"))
    op.alter_column('playlists', 'created_at',
                    server_default=sa.text("date_trunc('second', now())"))

    # Обрезаем миллисекунды у существующих записей
    op.execute("UPDATE users SET created_at = date_trunc('second', created_at)")
    op.execute("UPDATE playlists SET created_at = date_trunc('second', created_at)")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'created_at',
                    server_default=sa.text('now()'))
    op.alter_column('playlists', 'created_at',
                    server_default=sa.text('now()'))
