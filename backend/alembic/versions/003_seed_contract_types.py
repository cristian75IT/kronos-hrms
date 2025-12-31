"""Seed Contract Types

Revision ID: 003_seed_cont_types
Revises: 002_seed_data
Create Date: 2025-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_seed_cont_types'
down_revision = '002_seed_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Seed Contract Types
    op.execute("""
        INSERT INTO config.contract_types (id, code, name, description, is_part_time, part_time_percentage, annual_vacation_days, annual_rol_hours, annual_permit_hours, is_active)
        VALUES 
            (gen_random_uuid(), 'FT_IND', 'Full Time Indeterminato', 'Contratto a tempo indeterminato full time (40h)', false, 100.0, 26, 72, 0, true),
            (gen_random_uuid(), 'PT_50', 'Part Time 50%', 'Contratto part time 20h settimanali', true, 50.0, 26, 36, 0, true),
            (gen_random_uuid(), 'APP', 'Apprendistato', 'Contratto di apprendistato', false, 100.0, 26, 72, 0, true),
            (gen_random_uuid(), 'STG', 'Stage', 'Tirocinio formativo', false, 100.0, 0, 0, 0, true)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM config.contract_types WHERE code IN ('FT_IND', 'PT_50', 'APP', 'STG')")
