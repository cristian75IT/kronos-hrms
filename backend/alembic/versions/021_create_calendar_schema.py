"""021_create_calendar_schema

Revision ID: 021_create_calendar_schema
Revises: 020_seed_wallet_data
Create Date: 2026-01-02 10:30:00

Creates the Calendar microservice schema and tables.
Migrates holidays and closures from config schema.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '021_create_calendar_schema'
down_revision: Union[str, None] = '020_seed_wallet_data'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create calendar schema
    op.execute("CREATE SCHEMA IF NOT EXISTS calendar")
    
    # ═══════════════════════════════════════════════════════════
    # HOLIDAYS TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'holidays',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('scope', sa.String(20), server_default='national', nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('region_code', sa.String(10), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('recurrence_rule', sa.String(200), nullable=True),
        sa.Column('is_confirmed', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='calendar'
    )
    op.create_index('ix_calendar_holidays_date', 'holidays', ['date'], schema='calendar')
    op.create_index('ix_calendar_holidays_year', 'holidays', ['year'], schema='calendar')
    
    # ═══════════════════════════════════════════════════════════
    # CLOSURES TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'closures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('closure_type', sa.String(20), server_default='total', nullable=False),
        sa.Column('affected_departments', postgresql.JSONB(), nullable=True),
        sa.Column('affected_locations', postgresql.JSONB(), nullable=True),
        sa.Column('is_paid', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('consumes_leave_balance', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('leave_type_code', sa.String(10), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='calendar'
    )
    op.create_index('ix_calendar_closures_start_date', 'closures', ['start_date'], schema='calendar')
    op.create_index('ix_calendar_closures_end_date', 'closures', ['end_date'], schema='calendar')
    op.create_index('ix_calendar_closures_year', 'closures', ['year'], schema='calendar')
    
    # ═══════════════════════════════════════════════════════════
    # EVENTS TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('is_all_day', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('event_type', sa.String(30), server_default='generic', nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('visibility', sa.String(20), server_default='private', nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('is_virtual', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('meeting_url', sa.String(500), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('recurrence_rule', sa.String(200), nullable=True),
        sa.Column('parent_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('color', sa.String(7), server_default='#3B82F6', nullable=False),
        sa.Column('event_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), server_default='confirmed', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['parent_event_id'], ['calendar.events.id'], ondelete='CASCADE'),
        schema='calendar'
    )
    op.create_index('ix_calendar_events_start_date', 'events', ['start_date'], schema='calendar')
    op.create_index('ix_calendar_events_user_id', 'events', ['user_id'], schema='calendar')
    
    # ═══════════════════════════════════════════════════════════
    # EVENT PARTICIPANTS TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'event_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('response_status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('is_organizer', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_optional', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['calendar.events.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('event_id', 'user_id', name='uq_event_participant'),
        schema='calendar'
    )
    op.create_index('ix_calendar_event_participants_event_id', 'event_participants', ['event_id'], schema='calendar')
    op.create_index('ix_calendar_event_participants_user_id', 'event_participants', ['user_id'], schema='calendar')
    
    # ═══════════════════════════════════════════════════════════
    # WORKING DAY EXCEPTIONS TABLE
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'working_day_exceptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('exception_type', sa.String(20), nullable=False),
        sa.Column('reason', sa.String(200), nullable=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_code', sa.String(50), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='calendar'
    )
    op.create_index('ix_calendar_working_day_exceptions_date', 'working_day_exceptions', ['date'], schema='calendar')
    op.create_index('ix_calendar_working_day_exceptions_year', 'working_day_exceptions', ['year'], schema='calendar')
    
    # ═══════════════════════════════════════════════════════════
    # MIGRATE DATA FROM CONFIG SCHEMA (if exists)
    # ═══════════════════════════════════════════════════════════
    # Migrate holidays (only if source table exists and has data)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'config' AND table_name = 'holidays') THEN
                INSERT INTO calendar.holidays (id, name, date, year, scope, location_id, region_code, is_confirmed, is_active, created_at, updated_at)
                SELECT 
                    id, 
                    name, 
                    date, 
                    year, 
                    CASE 
                        WHEN is_national THEN 'national'
                        WHEN is_regional THEN 'regional'
                        ELSE 'company'
                    END as scope,
                    location_id,
                    region_code,
                    is_confirmed,
                    true as is_active,
                    created_at,
                    COALESCE(created_at, NOW()) as updated_at
                FROM config.holidays
                ON CONFLICT DO NOTHING;
            END IF;
        END $$;
    """)
    
    # Migrate closures (only if source table exists and has data)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'config' AND table_name = 'company_closures') THEN
                INSERT INTO calendar.closures (id, name, description, start_date, end_date, year, closure_type, 
                    affected_departments, affected_locations, is_paid, consumes_leave_balance, is_active, created_by, created_at, updated_at)
                SELECT 
                    id,
                    name,
                    description,
                    start_date,
                    end_date,
                    year,
                    closure_type,
                    affected_departments,
                    affected_locations,
                    is_paid,
                    consumes_leave_balance,
                    is_active,
                    created_by,
                    created_at,
                    COALESCE(updated_at, created_at, NOW()) as updated_at
                FROM config.company_closures
                ON CONFLICT DO NOTHING;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('working_day_exceptions', schema='calendar')
    op.drop_table('event_participants', schema='calendar')
    op.drop_table('events', schema='calendar')
    op.drop_table('closures', schema='calendar')
    op.drop_table('holidays', schema='calendar')
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS calendar CASCADE")
