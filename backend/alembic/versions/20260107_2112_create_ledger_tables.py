"""create enterprise ledger tables

Revision ID: 20260107_2112
Revises: 20260107_max_days
Create Date: 2026-01-07 21:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260107_2112'
down_revision: Union[str, None] = '20260107_max_days'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Time Ledger (Leaves)
    op.create_table(
        'time_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('entry_type', sa.String(30), nullable=False),
        sa.Column('balance_type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(6, 2), nullable=False),
        sa.Column('reference_type', sa.String(30), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_status', sa.String(20), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('amount >= 0', name='ck_time_ledger_amount_positive'),
        schema='leaves'
    )
    
    # Indexes for time_ledger
    op.create_index(
        'ix_time_ledger_user_year_type',
        'time_ledger',
        ['user_id', 'year', 'balance_type'],
        schema='leaves'
    )
    op.create_index(
        'ix_time_ledger_reference',
        'time_ledger',
        ['reference_type', 'reference_id'],
        schema='leaves'
    )
    
    # Expense Ledger
    op.create_table(
        'expense_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), index=True),
        sa.Column('entry_type', sa.String(30), nullable=False),
        sa.Column('category', sa.String(30)),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='EUR'),
        sa.Column('is_taxable', sa.Boolean(), default=False),
        sa.Column('vat_rate', sa.Numeric(5, 2)),
        sa.Column('vat_amount', sa.Numeric(12, 2)),
        sa.Column('is_reimbursable', sa.Boolean(), default=True),
        sa.Column('has_receipt', sa.Boolean(), default=True),
        sa.Column('compliance_notes', sa.Text()),
        sa.Column('reference_type', sa.String(30), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_status', sa.String(20), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('amount >= 0', name='ck_expense_ledger_amount_positive'),
        schema='expenses'
    )
    
    # Indexes for expense_ledger
    op.create_index(
        'ix_expense_ledger_trip',
        'expense_ledger',
        ['trip_id'],
        schema='expenses'
    )
    op.create_index(
        'ix_expense_ledger_reference',
        'expense_ledger',
        ['reference_type', 'reference_id'],
        schema='expenses'
    )


def downgrade() -> None:
    # Drop expense_ledger
    op.drop_index('ix_expense_ledger_reference', table_name='expense_ledger', schema='expenses')
    op.drop_index('ix_expense_ledger_trip', table_name='expense_ledger', schema='expenses')
    op.drop_table('expense_ledger', schema='expenses')
    
    # Drop time_ledger
    op.drop_index('ix_time_ledger_reference', table_name='time_ledger', schema='leaves')
    op.drop_index('ix_time_ledger_user_year_type', table_name='time_ledger', schema='leaves')
    op.drop_table('time_ledger', schema='leaves')
