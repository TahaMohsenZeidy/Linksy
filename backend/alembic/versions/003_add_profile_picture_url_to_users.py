"""add_profile_picture_url_to_users

Revision ID: 003
Revises: 002
Create Date: 2025-01-XX XX:XX:XX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add profile_picture_url column (nullable for backward compatibility)
    op.add_column('users', sa.Column('profile_picture_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove column
    op.drop_column('users', 'profile_picture_url')

