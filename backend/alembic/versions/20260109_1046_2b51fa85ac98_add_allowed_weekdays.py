"""add_allowed_weekdays

Revision ID: 2b51fa85ac98
Revises: 0cf3c087d0ff
Create Date: 2026-01-09 10:46:07.654308+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2b51fa85ac98'
down_revision: Union[str, None] = '0cf3c087d0ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sw_agreements', sa.Column('allowed_weekdays', postgresql.ARRAY(sa.Integer()), nullable=True, comment='0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday'), schema='smart_working')


def downgrade() -> None:
    op.drop_column('sw_agreements', 'allowed_weekdays', schema='smart_working')
