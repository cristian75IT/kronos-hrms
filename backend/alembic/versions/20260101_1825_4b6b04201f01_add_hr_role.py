"""add_hr_role

Revision ID: 4b6b04201f01
Revises: 015_link_ced_modes
Create Date: 2026-01-01 18:25:30.065794+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b6b04201f01'
down_revision: Union[str, None] = '015_link_ced_modes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_hr', sa.Boolean(), nullable=False, server_default=sa.text('false')), schema='auth')


def downgrade() -> None:
    op.drop_column('users', 'is_hr', schema='auth')
