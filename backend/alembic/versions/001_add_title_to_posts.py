"""add_title_to_posts

Revision ID: 001
Revises: 
Create Date: 2024-11-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add title column to posts table
    # Note: If table already has data, existing posts will get 'Untitled' as default
    op.add_column('posts', sa.Column('title', sa.String(length=200), nullable=False, server_default='Untitled'))


def downgrade() -> None:
    # Remove title column from posts table
    op.drop_column('posts', 'title')

