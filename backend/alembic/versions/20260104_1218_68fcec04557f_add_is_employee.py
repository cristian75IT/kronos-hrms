"""add_is_employee

Revision ID: 68fcec04557f
Revises: 032_add_target_role_ids
Create Date: 2026-01-04 12:18:52.957869+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68fcec04557f'
down_revision: Union[str, None] = '032_add_target_role_ids'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_employee', sa.Boolean(), nullable=False, server_default='true'), schema='auth')


def downgrade() -> None:
    op.drop_column('users', 'is_employee', schema='auth')
