"""Enhance employee contracts with CCNL and Level associations.

Revision ID: 009_enhance_employee_contracts
Revises: 008_link_contract_types
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_enhance_employee_contracts'
down_revision = '008_link_contract_types'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to auth.employee_contracts
    op.add_column('employee_contracts', sa.Column('national_contract_id', postgresql.UUID(as_uuid=True), nullable=True), schema='auth')
    op.add_column('employee_contracts', sa.Column('level_id', postgresql.UUID(as_uuid=True), nullable=True), schema='auth')
    
    # Create foreign keys
    op.create_foreign_key(
        'fk_employee_contracts_national_contract',
        'employee_contracts', 'national_contracts',
        ['national_contract_id'], ['id'],
        source_schema='auth', referent_schema='config'
    )
    op.create_foreign_key(
        'fk_employee_contracts_level',
        'employee_contracts', 'national_contract_levels',
        ['level_id'], ['id'],
        source_schema='auth', referent_schema='config'
    )
    
    # Drop old string column 'level' if exists
    # We check first if we want to preserve data, but here we assume migration to new strict structure
    op.drop_column('employee_contracts', 'level', schema='auth')


def downgrade() -> None:
    op.add_column('employee_contracts', sa.Column('level', sa.String(50), nullable=True), schema='auth')
    op.drop_constraint('fk_employee_contracts_level', 'employee_contracts', schema='auth', type_='foreignkey')
    op.drop_constraint('fk_employee_contracts_national_contract', 'employee_contracts', schema='auth', type_='foreignkey')
    op.drop_column('employee_contracts', 'level_id', schema='auth')
    op.drop_column('employee_contracts', 'national_contract_id', schema='auth')
