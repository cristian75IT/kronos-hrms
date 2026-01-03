"""enterprise_calendar_refactor

Revision ID: 51a7fa722a97
Revises: 030_hr_reporting
Create Date: 2026-01-03 06:05:55.361903+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '51a7fa722a97'
down_revision: Union[str, None] = '030_hr_reporting'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. CLEANUP (Idempotency Ensure)
    op.execute("DROP TABLE IF EXISTS calendar.calendar_shares CASCADE")
    op.execute("DROP TABLE IF EXISTS calendar.location_calendars CASCADE")
    op.execute("DROP TABLE IF EXISTS calendar.holiday_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS calendar.work_week_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS calendar.calendars CASCADE")  # Unified table
    
    op.execute("ALTER TABLE calendar.holidays DROP COLUMN IF EXISTS profile_id CASCADE")
    op.execute("ALTER TABLE calendar.holidays DROP COLUMN IF EXISTS recurrence_rule CASCADE")
    
    op.execute("DROP TYPE IF EXISTS calendar.calendartype CASCADE")
    op.execute("DROP TYPE IF EXISTS calendar.calendarpermission CASCADE")

    # 1. Create Work Week Profiles
    op.create_table('work_week_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weekly_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('total_weekly_hours', sa.Numeric(precision=5, scale=2), nullable=False, server_default='40.0'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        schema='calendar'
    )

    # 2. Create Calendars (Unified Table)
    op.create_table('calendars',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('SYSTEM', 'LOCATION', 'PERSONAL', 'TEAM', name='calendartype', schema='calendar'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=False, server_default='#4F46E5'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='calendar'
    )
    op.create_index(op.f('ix_calendar_calendars_owner_id'), 'calendars', ['owner_id'], unique=False, schema='calendar')

    # 3. Create Holiday Profiles
    op.create_table('holiday_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calendar_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('region_code', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendar.calendars.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('calendar_id'),
        schema='calendar'
    )

    # 4. Create Location Calendars
    op.create_table('location_calendars',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_week_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='Europe/Rome'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['work_week_profile_id'], ['calendar.work_week_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('location_id', name='uq_location_calendar'),
        schema='calendar'
    )
    op.create_index(op.f('ix_calendar_location_calendars_location_id'), 'location_calendars', ['location_id'], unique=False, schema='calendar')

    # 5. Create Calendar Shares
    op.create_table('calendar_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('calendar_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission', sa.Enum('READ', 'WRITE', 'ADMIN', name='calendarpermission', schema='calendar'), nullable=False, server_default='READ'),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendar.calendars.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('calendar_id', 'user_id', name='uq_calendar_share_user'),
        schema='calendar'
    )
    op.create_index(op.f('ix_calendar_calendar_shares_user_id'), 'calendar_shares', ['user_id'], unique=False, schema='calendar')

    # 6. Update Holidays Table
    op.add_column('holidays', sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=True), schema='calendar')
    op.add_column('holidays', sa.Column('recurrence_rule', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='calendar')
    op.create_index(op.f('ix_calendar_holidays_profile_id'), 'holidays', ['profile_id'], unique=False, schema='calendar')
    op.create_foreign_key(None, 'holidays', 'holiday_profiles', ['profile_id'], ['id'], source_schema='calendar', referent_schema='calendar', ondelete='CASCADE')
    
    op.drop_column('holidays', 'year', schema='calendar')
    op.drop_column('holidays', 'scope', schema='calendar')
    op.drop_column('holidays', 'location_id', schema='calendar')
    op.drop_column('holidays', 'region_code', schema='calendar')

    # 7. Update Events Table
    op.execute("ALTER TABLE calendar.events DROP CONSTRAINT IF EXISTS events_calendar_id_fkey") # Drop specific legacy
    op.execute("TRUNCATE TABLE calendar.events CASCADE")
    op.create_foreign_key(None, 'events', 'calendars', ['calendar_id'], ['id'], source_schema='calendar', referent_schema='calendar', ondelete='CASCADE')
    
    # 8. Drop old User Calendars table with CASCADE
    op.execute("DROP TABLE IF EXISTS calendar.user_calendars CASCADE")


def downgrade() -> None:
    # Reverse operations
    op.create_table('user_calendars',
        sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column('user_id', postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column('name', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
        sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column('color', sa.VARCHAR(length=7), server_default=sa.text("'#4F46E5'::character varying"), autoincrement=False, nullable=False),
        sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name='user_calendars_pkey'),
        schema='calendar'
    )
    
    op.drop_constraint(None, 'events', schema='calendar', type_='foreignkey')
    
    op.add_column('holidays', sa.Column('region_code', sa.VARCHAR(length=10), autoincrement=False, nullable=True), schema='calendar')
    op.add_column('holidays', sa.Column('location_id', postgresql.UUID(), autoincrement=False, nullable=True), schema='calendar')
    op.add_column('holidays', sa.Column('scope', sa.VARCHAR(length=20), server_default=sa.text("'national'::character varying"), autoincrement=False, nullable=False), schema='calendar')
    op.add_column('holidays', sa.Column('year', sa.INTEGER(), autoincrement=False, nullable=False), schema='calendar')
    
    op.drop_constraint(None, 'holidays', schema='calendar', type_='foreignkey')
    op.drop_index(op.f('ix_calendar_holidays_profile_id'), table_name='holidays', schema='calendar')
    op.drop_column('holidays', 'recurrence_rule', schema='calendar')
    op.drop_column('holidays', 'profile_id', schema='calendar')
    
    op.drop_table('calendar_shares', schema='calendar')
    op.drop_table('location_calendars', schema='calendar')
    op.drop_table('holiday_profiles', schema='calendar')
    op.drop_table('calendars', schema='calendar')
    op.drop_table('work_week_profiles', schema='calendar')
