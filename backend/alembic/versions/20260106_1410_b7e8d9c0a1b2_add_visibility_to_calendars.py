"""add_visibility_to_calendars

Revision ID: b7e8d9c0a1b2
Revises: 13fc1384cf25
Create Date: 2026-01-06 14:10:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e8d9c0a1b2'
down_revision: Union[str, None] = '13fc1384cf25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add column visibility to calendars
    op.add_column('calendars', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private'), schema='calendar')


def downgrade() -> None:
    # Remove column visibility from calendars
    op.drop_column('calendars', 'visibility', schema='calendar')
