"""Add calculation modes table

Revision ID: 013_calculation_modes
Revises: 012_notification_settings
Create Date: 2026-01-01 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_calculation_modes'
down_revision = '012_notification_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create calculation_modes table
    op.create_table(
        'calculation_modes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('function_name', sa.String(length=50), nullable=False),
        sa.Column('default_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        schema='config'
    )

    # Add columns to national_contract_versions
    op.add_column('national_contract_versions', sa.Column('vacation_calc_mode_id', postgresql.UUID(as_uuid=True), nullable=True), schema='config')
    op.add_column('national_contract_versions', sa.Column('rol_calc_mode_id', postgresql.UUID(as_uuid=True), nullable=True), schema='config')
    op.add_column('national_contract_versions', sa.Column('vacation_calc_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='config')
    op.add_column('national_contract_versions', sa.Column('rol_calc_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='config')

    # Add FKs
    op.create_foreign_key(None, 'national_contract_versions', 'calculation_modes', ['vacation_calc_mode_id'], ['id'], source_schema='config', referent_schema='config')
    op.create_foreign_key(None, 'national_contract_versions', 'calculation_modes', ['rol_calc_mode_id'], ['id'], source_schema='config', referent_schema='config')
    
    # Pre-seed default modes
    op.execute("""
        INSERT INTO config.calculation_modes (id, name, code, function_name, default_parameters)
        VALUES 
        (gen_random_uuid(), 'Mensile Standard (1/12)', 'MONTHLY_STD', 'monthly_std', '{}'),
        (gen_random_uuid(), 'Giornaliero (su 260gg)', 'DAILY_260', 'daily_260', '{"divisor": 260}'),
        (gen_random_uuid(), 'Giornaliero (su 365gg)', 'DAILY_365', 'daily_365', '{"divisor": 365}'),
        (gen_random_uuid(), 'Annuale Fisso', 'YEARLY_FLAT', 'yearly_flat', '{}')
    """)


def downgrade() -> None:
    op.drop_column('national_contract_versions', 'rol_calc_params', schema='config')
    op.drop_column('national_contract_versions', 'vacation_calc_params', schema='config')
    op.drop_column('national_contract_versions', 'rol_calc_mode_id', schema='config')
    op.drop_column('national_contract_versions', 'vacation_calc_mode_id', schema='config')
    op.drop_table('calculation_modes', schema='config')
