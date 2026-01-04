"""Add scope to role permissions

Revision ID: 3af2dbb3fd4b
Revises: 0b2de4798954
Create Date: 2026-01-04 14:08:00.785076+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3af2dbb3fd4b'
down_revision: Union[str, None] = '0b2de4798954'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add scope column to role_permissions table
    op.add_column('role_permissions', sa.Column('scope', sa.String(), nullable=False, server_default='GLOBAL'), schema='auth')
    
    # Update PK to include scope
    op.drop_constraint('role_permissions_pkey', 'role_permissions', schema='auth')
    op.create_primary_key('role_permissions_pkey', 'role_permissions', ['role_id', 'permission_id', 'scope'], schema='auth')


def downgrade() -> None:
    # Revert PK
    op.drop_constraint('role_permissions_pkey', 'role_permissions', schema='auth')
    op.create_primary_key('role_permissions_pkey', 'role_permissions', ['role_id', 'permission_id'], schema='auth')
    
    # Drop scope column
    op.drop_column('role_permissions', 'scope', schema='auth')
