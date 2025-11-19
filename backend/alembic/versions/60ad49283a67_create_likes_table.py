"""create_likes_table

Revision ID: 60ad49283a67
Revises: 004
Create Date: 2025-11-06 22:54:45.760792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60ad49283a67'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists using raw SQL (to avoid transaction issues)
    # Table might have been created by Base.metadata.create_all on startup
    from sqlalchemy import text
    
    conn = op.get_bind()
    result = conn.execute(text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'likes')"
    ))
    table_exists = result.scalar()
    
    if not table_exists:
        # Create likes table
        op.create_table(
            'likes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like')
        )
        op.create_index(op.f('ix_likes_id'), 'likes', ['id'], unique=False)


def downgrade() -> None:
    # Drop likes table
    op.drop_index(op.f('ix_likes_id'), table_name='likes')
    op.drop_table('likes')

