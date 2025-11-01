"""add_password_hash_to_users

Revision ID: e89b0ad54a9a
Revises: e74910e379b6
Create Date: 2025-11-01 22:34:27.936126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e89b0ad54a9a'
down_revision: Union[str, Sequence[str], None] = 'e74910e379b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'password_hash')
