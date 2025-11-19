"""add_image_url_to_posts

Revision ID: 005
Revises: 60ad49283a67
Create Date: 2025-01-XX XX:XX:XX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '60ad49283a67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add image_url column to posts table (nullable for backward compatibility)
    op.add_column('posts', sa.Column('image_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove column
    op.drop_column('posts', 'image_url')

