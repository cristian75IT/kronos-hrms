"""022_add_user_calendars

Revision ID: 022_add_user_calendars
Revises: b49418a1226b
Create Date: 2026-01-02 14:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '022_add_user_calendars'
down_revision: Union[str, None] = '021_create_calendar_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create user_calendars table
    op.create_table(
        'user_calendars',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), server_default='#4F46E5', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='calendar'
    )
    op.create_index('ix_calendar_user_calendars_user_id', 'user_calendars', ['user_id'], schema='calendar')
    
    # Add calendar_id to events
    op.add_column('events', sa.Column('calendar_id', postgresql.UUID(as_uuid=True), nullable=True), schema='calendar')
    op.create_index('ix_calendar_events_calendar_id', 'events', ['calendar_id'], schema='calendar')
    op.create_foreign_key(
        'fk_calendar_events_calendar_id',
        'events', 'user_calendars',
        ['calendar_id'], ['id'],
        source_schema='calendar', referent_schema='calendar',
        ondelete='SET NULL'
    )

def downgrade() -> None:
    op.drop_constraint('fk_calendar_events_calendar_id', 'events', schema='calendar', type_='foreignkey')
    op.drop_index('ix_calendar_events_calendar_id', table_name='events', schema='calendar')
    op.drop_column('events', 'calendar_id', schema='calendar')
    op.drop_table('user_calendars', schema='calendar')
