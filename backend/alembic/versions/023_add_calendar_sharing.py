"""add calendar sharing

Revision ID: 023_add_calendar_sharing
Revises: 022_add_user_calendars
Create Date: 2026-01-02 13:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '023_add_calendar_sharing'
down_revision = '022_add_user_calendars'
branch_labels = None
depends_on = None


def upgrade():
    # Create calendar_shares table
    op.create_table(
        'calendar_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calendar_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_with_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('can_edit', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendar.user_calendars.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('calendar_id', 'shared_with_user_id', name='uq_calendar_share'),
        schema='calendar'
    )
    op.create_index(op.f('ix_calendar_calendar_shares_calendar_id'), 'calendar_shares', ['calendar_id'], unique=False, schema='calendar')
    op.create_index(op.f('ix_calendar_calendar_shares_shared_with_user_id'), 'calendar_shares', ['shared_with_user_id'], unique=False, schema='calendar')


def downgrade():
    op.drop_table('calendar_shares', schema='calendar')
