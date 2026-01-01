"""Add regional holidays and confirmation fields

Revision ID: 005_holiday_enhancements
Revises: 004_national_contracts
Create Date: 2026-01-01 11:05:00.000000

Adds support for regional holidays (Sardegna) and year-to-year confirmation mechanism.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_holiday_enhancements'
down_revision = '004_national_contracts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to holidays table
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'holidays' AND column_name = 'is_regional'
            ) THEN
                ALTER TABLE config.holidays ADD COLUMN is_regional BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'holidays' AND column_name = 'region_code'
            ) THEN
                ALTER TABLE config.holidays ADD COLUMN region_code VARCHAR(10);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'holidays' AND column_name = 'is_confirmed'
            ) THEN
                ALTER TABLE config.holidays ADD COLUMN is_confirmed BOOLEAN DEFAULT TRUE;
            END IF;
        END $$;
    """)
    
    # Set all existing holidays as confirmed
    op.execute("UPDATE config.holidays SET is_confirmed = TRUE WHERE is_confirmed IS NULL")
    
    # Add index for efficient querying by year and type
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE schemaname = 'config' AND indexname = 'ix_holidays_year_type'
            ) THEN
                CREATE INDEX ix_holidays_year_type ON config.holidays (year, is_national, is_regional);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS config.ix_holidays_year_type")
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'holidays' AND column_name = 'is_regional'
            ) THEN
                ALTER TABLE config.holidays DROP COLUMN is_regional;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'holidays' AND column_name = 'region_code'
            ) THEN
                ALTER TABLE config.holidays DROP COLUMN region_code;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'config' AND table_name = 'holidays' AND column_name = 'is_confirmed'
            ) THEN
                ALTER TABLE config.holidays DROP COLUMN is_confirmed;
            END IF;
        END $$;
    """)
