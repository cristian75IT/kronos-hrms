"""Link Contract Types to CCNL Versions

Revision ID: 008_link_contract_types
Revises: 007_contract_levels
Create Date: 2026-01-01 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_link_contract_types'
down_revision = '007_contract_levels'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # National Contract Type Configs
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        'national_contract_type_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('national_contract_version_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('config.national_contract_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contract_type_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('config.contract_types.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('weekly_hours', sa.Float, nullable=False),
        sa.Column('annual_vacation_days', sa.Integer, nullable=False),
        sa.Column('annual_rol_hours', sa.Integer, nullable=False),
        sa.Column('annual_ex_festivita_hours', sa.Integer, nullable=False),
        sa.Column('description', sa.String(200), nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.UniqueConstraint('national_contract_version_id', 'contract_type_id', name='uq_nc_version_contract_type'),
        schema='config'
    )
    
    op.create_index(
        'ix_nctc_version_id',
        'national_contract_type_configs',
        ['national_contract_version_id'],
        schema='config'
    )

    # ═══════════════════════════════════════════════════════════════════
    # Seed Configs for CCNL CED
    # ═══════════════════════════════════════════════════════════════════
    op.execute("""
        INSERT INTO config.national_contract_type_configs 
            (id, national_contract_version_id, contract_type_id, weekly_hours, annual_vacation_days, annual_rol_hours, annual_ex_festivita_hours, description)
        SELECT 
            gen_random_uuid(),
            v.id,
            ct.id,
            CASE 
                WHEN ct.is_part_time THEN (v.weekly_hours_full_time * ct.part_time_percentage / 100)
                ELSE v.weekly_hours_full_time
            END,
            v.annual_vacation_days,
            CASE 
                WHEN ct.is_part_time THEN CAST((v.annual_rol_hours * ct.part_time_percentage / 100) AS INTEGER)
                ELSE v.annual_rol_hours
            END,
            CASE 
                WHEN ct.is_part_time THEN CAST((v.annual_ex_festivita_hours * ct.part_time_percentage / 100) AS INTEGER)
                ELSE v.annual_ex_festivita_hours
            END,
            ct.name
        FROM config.national_contract_versions v
        CROSS JOIN config.contract_types ct
        JOIN config.national_contracts nc ON v.national_contract_id = nc.id
        WHERE nc.code = 'CCNL_CED' AND ct.is_active = true
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('national_contract_type_configs', schema='config')
