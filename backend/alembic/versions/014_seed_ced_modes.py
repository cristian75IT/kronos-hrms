"""Seed CED Calculation Modes

Revision ID: 014_seed_ced_modes
Revises: 013_calculation_modes
Create Date: 2026-01-01 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json
import uuid

# revision identifiers, used by Alembic.
revision = '014_seed_ced_modes'
down_revision = '013_calculation_modes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Define table for bulk_insert
    metadata = sa.MetaData()
    calculation_modes = sa.Table(
        'calculation_modes',
        metadata,
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String()),
        sa.Column('code', sa.String()),
        sa.Column('description', sa.Text()),
        sa.Column('function_name', sa.String()),
        sa.Column('default_parameters', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('is_active', sa.Boolean()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='config'
    )
    
    modes_to_insert = [
        {
            "id": uuid.uuid4(), # Pass UUID object
            "name": "Standard Mensile (CCNL CED)",
            "code": "MONTHLY_CED_STD",
            "description": "Maturazione 1/12 mensile standard specifico per CCNL CED",
            "function_name": "calculate_accrual_monthly_std",
            "default_parameters": {"divisors": {"vacation": 12, "rol": 12}}, # Pass dict
            "is_active": True
        },
        {
            "id": uuid.uuid4(),
            "name": "Giornaliero 1/365 (Opzione)",
            "code": "DAILY_365",
            "description": "Maturazione giornaliera su base annua (1/365)",
            "function_name": "calculate_accrual_daily_365",
            "default_parameters": {"year_basis": 365},
            "is_active": True
        }
    ]
    
    connection = op.get_bind()
    
    for mode in modes_to_insert:
        code = mode['code']
        # Check if exists
        exists = connection.execute(sa.text(f"SELECT 1 FROM config.calculation_modes WHERE code = '{code}'")).scalar()
        if not exists:
            op.bulk_insert(calculation_modes, [mode])


def downgrade() -> None:
    op.execute("DELETE FROM config.calculation_modes WHERE code IN ('MONTHLY_CED_STD', 'DAILY_365')")
