"""add_keycloak_fields_to_users

Revision ID: 002
Revises: 001
Create Date: 2025-11-06 16:21:03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add keycloak_user_id column (nullable for backward compatibility)
    op.add_column('users', sa.Column('keycloak_user_id', sa.String(), nullable=True))
    
    # Add last_synced_at column (nullable)
    op.add_column('users', sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    
    # Create unique index on keycloak_user_id for fast lookups
    # Note: unique=True ensures one Keycloak user maps to one app user
    op.create_index('ix_users_keycloak_user_id', 'users', ['keycloak_user_id'], unique=True)


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_users_keycloak_user_id', table_name='users')
    
    # Remove columns
    op.drop_column('users', 'last_synced_at')
    op.drop_column('users', 'keycloak_user_id')

