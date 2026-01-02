"""add_trip_wallet_tables

Revision ID: 019_add_trip_wallets
Revises: b49418a1226b
Create Date: 2026-01-02 09:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '019_add_trip_wallets'
down_revision: Union[str, None] = 'b49418a1226b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cleanup in case they already exist
    op.execute("DROP TABLE IF EXISTS wallet.trip_wallet_transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS wallet.trip_wallets CASCADE")

    # Add missing columns to employee_wallets (previously in time_wallet schema, now unified)
    op.add_column('employee_wallets', sa.Column('legal_minimum_required', sa.Numeric(precision=5, scale=2), server_default='20', nullable=False), schema='wallet')
    op.add_column('employee_wallets', sa.Column('legal_minimum_taken', sa.Numeric(precision=5, scale=2), server_default='0', nullable=False), schema='wallet')
    op.add_column('employee_wallets', sa.Column('hourly_rate_snapshot', sa.Numeric(precision=10, scale=2), nullable=True), schema='wallet')
    op.add_column('employee_wallets', sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False), schema='wallet')

    # Add missing columns to wallet_transactions (previously in time_wallet schema, now unified)
    op.add_column('wallet_transactions', sa.Column('category', sa.String(length=30), nullable=True), schema='wallet')
    op.add_column('wallet_transactions', sa.Column('monetary_value', sa.Numeric(precision=12, scale=2), nullable=True), schema='wallet')
    op.add_column('wallet_transactions', sa.Column('exchange_rate_to_hours', sa.Numeric(precision=10, scale=4), nullable=True), schema='wallet')

    # Trip Wallets table
    op.create_table(
        'trip_wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_budget', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('total_advances', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('total_expenses', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('total_taxable', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('total_non_taxable', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('currency', sa.String(3), server_default='EUR', nullable=False),
        sa.Column('status', sa.String(20), server_default='OPEN', nullable=False),
        sa.Column('policy_violations_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_reconciled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='wallet'
    )
    op.create_index('ix_wallet_trip_wallets_trip_id', 'trip_wallets', ['trip_id'], unique=True, schema='wallet')
    op.create_index('ix_wallet_trip_wallets_user_id', 'trip_wallets', ['user_id'], schema='wallet')

    # Trip Wallet Transactions table
    op.create_table(
        'trip_wallet_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wallet.trip_wallets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('category', sa.String(30), nullable=True),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('tax_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('is_reimbursable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_taxable', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('has_receipt', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('compliance_flags', sa.Text(), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='wallet'
    )


def downgrade() -> None:
    op.drop_table('trip_wallet_transactions', schema='wallet')
    op.drop_table('trip_wallets', schema='wallet')
