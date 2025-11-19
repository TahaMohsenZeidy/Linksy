"""create_comments_table

Revision ID: 004
Revises: 003
Create Date: 2025-01-XX XX:XX:XX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists using raw SQL (to avoid transaction issues)
    # Table might have been created by Base.metadata.create_all on startup
    conn = op.get_bind()
    result = conn.execute(text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'comments')"
    ))
    table_exists = result.scalar()
    
    if not table_exists:
        # Create comments table
        op.create_table(
            'comments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    else:
        # Table already exists, just ensure the index exists
        try:
            op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
        except Exception:
            # Index might already exist, that's okay
            pass


def downgrade() -> None:
    # Drop comments table
    op.drop_index(op.f('ix_comments_id'), table_name='comments')
    op.drop_table('comments')

