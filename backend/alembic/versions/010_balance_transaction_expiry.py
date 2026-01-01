"""Add expiry_date to balance_transactions

Revision ID: 010_balance_transaction_expiry
Revises: 009_enhance_employee_contracts
Create Date: 2024-01-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_balance_transaction_expiry'
down_revision = '009_enhance_employee_contracts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add expiry_date to balance_transactions
    op.add_column('balance_transactions', sa.Column('expiry_date', sa.Date(), nullable=True), schema='leaves')


def downgrade() -> None:
    op.drop_column('balance_transactions', 'expiry_date', schema='leaves')
