"""Migrate holidays and closures from config schema to calendar schema.

This migration consolidates holidays and closures into the Calendar Service
as the single source of truth.

Revision ID: 026_migrate_holidays_closures
Revises: 025_enterprise_notifications
Create Date: 2026-01-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '026_migrate_holidays_closures'
down_revision: str = '025_enterprise_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate data from config.holidays and config.company_closures to calendar schema.
    
    After migration, the config tables are deprecated but kept for backward compatibility.
    """
    conn = op.get_bind()
    
    # ═══════════════════════════════════════════════════════════
    # MIGRATE HOLIDAYS
    # ═══════════════════════════════════════════════════════════
    
    # Check if config.holidays has data
    result = conn.execute(text("SELECT COUNT(*) FROM config.holidays"))
    config_holiday_count = result.scalar()
    
    if config_holiday_count > 0:
        print(f"Migrating {config_holiday_count} holidays from config.holidays to calendar.holidays...")
        
        # Insert holidays that don't already exist (by date + name combination for the same year)
        conn.execute(text("""
            INSERT INTO calendar.holidays (
                id, name, description, date, year, scope, location_id, region_code,
                is_recurring, recurrence_rule, is_confirmed, is_active, created_at, updated_at
            )
            SELECT 
                ch.id,
                ch.name,
                NULL,  -- description (not in config.holidays)
                ch.date,
                ch.year,
                CASE 
                    WHEN ch.is_national THEN 'national'
                    WHEN ch.is_regional THEN 'regional'
                    WHEN ch.location_id IS NOT NULL THEN 'local'
                    ELSE 'national'
                END,
                ch.location_id,
                ch.region_code,
                FALSE,  -- is_recurring
                NULL,   -- recurrence_rule
                ch.is_confirmed,
                TRUE,   -- is_active
                ch.created_at,
                ch.created_at
            FROM config.holidays ch
            WHERE NOT EXISTS (
                SELECT 1 FROM calendar.holidays cal
                WHERE cal.date = ch.date 
                AND cal.name = ch.name 
                AND cal.year = ch.year
            )
        """))
        
        print("Holiday migration complete.")
    else:
        print("No holidays to migrate from config.holidays.")
    
    # ═══════════════════════════════════════════════════════════
    # MIGRATE COMPANY CLOSURES
    # ═══════════════════════════════════════════════════════════
    
    # Check if config.company_closures has data
    result = conn.execute(text("SELECT COUNT(*) FROM config.company_closures"))
    config_closure_count = result.scalar()
    
    if config_closure_count > 0:
        print(f"Migrating {config_closure_count} closures from config.company_closures to calendar.closures...")
        
        # Insert closures that don't already exist
        conn.execute(text("""
            INSERT INTO calendar.closures (
                id, name, description, start_date, end_date, year, 
                closure_type, affected_departments, affected_locations,
                is_paid, consumes_leave_balance, leave_type_code,
                is_active, created_by, created_at, updated_at
            )
            SELECT 
                cc.id,
                cc.name,
                cc.description,
                cc.start_date,
                cc.end_date,
                cc.year,
                cc.closure_type,
                cc.affected_departments,
                cc.affected_locations,
                cc.is_paid,
                cc.consumes_leave_balance,
                NULL,  -- leave_type_code (need to resolve from leave_type_id if needed)
                cc.is_active,
                cc.created_by,
                cc.created_at,
                cc.updated_at
            FROM config.company_closures cc
            WHERE NOT EXISTS (
                SELECT 1 FROM calendar.closures cal
                WHERE cal.start_date = cc.start_date 
                AND cal.end_date = cc.end_date 
                AND cal.name = cc.name
                AND cal.year = cc.year
            )
        """))
        
        print("Closure migration complete.")
    else:
        print("No closures to migrate from config.company_closures.")
    
    # ═══════════════════════════════════════════════════════════
    # ADD DEPRECATION COMMENTS TO CONFIG TABLES
    # ═══════════════════════════════════════════════════════════
    
    conn.execute(text("""
        COMMENT ON TABLE config.holidays IS 
        'DEPRECATED: Data migrated to calendar.holidays. Use Calendar Service for all holiday operations.';
    """))
    
    conn.execute(text("""
        COMMENT ON TABLE config.company_closures IS 
        'DEPRECATED: Data migrated to calendar.closures. Use Calendar Service for all closure operations.';
    """))
    
    print("Migration complete. Config tables are now deprecated.")


def downgrade() -> None:
    """No downgrade - data migration is one-way.
    
    If needed, restore from backup or re-seed data.
    """
    # Remove deprecation comments
    conn = op.get_bind()
    
    conn.execute(text("""
        COMMENT ON TABLE config.holidays IS 
        'Holiday calendar. Stores national, regional, and local holidays.';
    """))
    
    conn.execute(text("""
        COMMENT ON TABLE config.company_closures IS 
        'Company closure calendar. Stores company-wide closures.';
    """))
    
    print("Deprecation comments removed. Note: Data was NOT migrated back.")
