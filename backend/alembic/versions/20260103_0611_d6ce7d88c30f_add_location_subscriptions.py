"""add_location_subscriptions

Revision ID: d6ce7d88c30f
Revises: 51a7fa722a97
Create Date: 2026-01-03 06:11:47.398358+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd6ce7d88c30f'
down_revision: Union[str, None] = '51a7fa722a97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Location Subscriptions table
    op.create_table('location_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_calendar_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calendar_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendar.calendars.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_calendar_id'], ['calendar.location_calendars.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('location_id', 'calendar_id', name='uq_location_subscription'),
        schema='calendar'
    )


def downgrade() -> None:
    op.drop_table('location_subscriptions', schema='calendar')
