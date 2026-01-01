"""Add remaining_amount to balance_transactions

Revision ID: 011_balance_tx_remaining
Revises: 010_balance_transaction_expiry
Create Date: 2024-01-01 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_balance_tx_remaining'
down_revision = '010_balance_transaction_expiry'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add remaining_amount and update balance_after precision
    op.add_column('balance_transactions', sa.Column('remaining_amount', sa.Numeric(precision=6, scale=2), server_default='0', nullable=False), schema='leaves')
    op.alter_column('balance_transactions', 'balance_after',
               existing_type=sa.NUMERIC(precision=6, scale=2),
               type_=sa.NUMERIC(precision=7, scale=2),
               existing_nullable=False,
               schema='leaves')
    
    # Initialize remaining_amount with amount for older entries if positive
    op.execute("UPDATE leaves.balance_transactions SET remaining_amount = amount WHERE amount > 0")


def downgrade() -> None:
    op.alter_column('balance_transactions', 'balance_after',
               existing_type=sa.NUMERIC(precision=7, scale=2),
               type_=sa.NUMERIC(precision=6, scale=2),
               existing_nullable=False,
               schema='leaves')
    op.drop_column('balance_transactions', 'remaining_amount', schema='leaves')
