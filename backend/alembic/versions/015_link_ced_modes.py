"""Link CED Modes to Contracts

Revision ID: 015_link_ced_modes
Revises: 014_seed_ced_modes
Create Date: 2026-01-01 19:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_link_ced_modes'
down_revision = '014_seed_ced_modes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    
    # 1. Get Mode ID
    mode_id = conn.execute(
        sa.text("SELECT id FROM config.calculation_modes WHERE code = 'MONTHLY_CED_STD'")
    ).scalar()
    
    if not mode_id:
        # Fallback to MONTHLY_STD if CED specific not found
        mode_id = conn.execute(
            sa.text("SELECT id FROM config.calculation_modes WHERE code = 'MONTHLY_STD'")
        ).scalar()
        
    if mode_id:
        # 2. Update Contracts matching 'CED'
        # Use Python string injection for UUID is safe if we quote it, 
        # or use bindparams. Bindparams is better.
        
        op.execute(
            sa.text("""
            UPDATE config.national_contract_versions ncv
            SET vacation_calc_mode_id = :mode_id,
                rol_calc_mode_id = :mode_id
            FROM config.national_contracts nc
            WHERE ncv.national_contract_id = nc.id
            AND nc.name ILIKE '%CED%'
            """).bindparams(mode_id=mode_id)
        )

def downgrade() -> None:
    op.execute("""
    UPDATE config.national_contract_versions ncv
    SET vacation_calc_mode_id = NULL,
        rol_calc_mode_id = NULL
    FROM config.national_contracts nc
    WHERE ncv.national_contract_id = nc.id
    AND nc.name ILIKE '%CED%'
    """)
