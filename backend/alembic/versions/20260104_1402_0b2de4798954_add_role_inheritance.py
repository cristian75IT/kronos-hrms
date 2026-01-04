"""Add role inheritance

Revision ID: 0b2de4798954
Revises: rbac_v1
Create Date: 2026-01-04 14:02:22.012890+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b2de4798954'
down_revision: Union[str, None] = 'rbac_v1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add parent_id column to roles table in auth schema
    op.add_column('roles', sa.Column('parent_id', sa.UUID(), nullable=True), schema='auth')
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_roles_parent_id',
        'roles', 'roles',
        ['parent_id'], ['id'],
        source_schema='auth', 
        referent_schema='auth',
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_roles_parent_id', 'roles', schema='auth', type_='foreignkey')
    
    # Drop parent_id column
    op.drop_column('roles', 'parent_id', schema='auth')
