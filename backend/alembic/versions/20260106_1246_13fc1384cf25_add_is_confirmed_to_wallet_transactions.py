"""add_is_confirmed_to_wallet_transactions

Revision ID: 13fc1384cf25
Revises: 6a7b8c9d0e1f
Create Date: 2026-01-06 12:46:34.892716+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '13fc1384cf25'
down_revision: Union[str, None] = '6a7b8c9d0e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to wallet_transactions
    op.add_column('wallet_transactions', sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='true'), schema='time_wallet')
    op.add_column('wallet_transactions', sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='time_wallet')
    
    # Fix index name for employee_wallets if needed (Alembic detected a change)
    op.drop_index('ix_wallet_employee_wallets_user_id', table_name='employee_wallets', schema='time_wallet')
    op.create_index(op.f('ix_time_wallet_employee_wallets_user_id'), 'employee_wallets', ['user_id'], unique=False, schema='time_wallet')


def downgrade() -> None:
    # Revert index change
    op.drop_index(op.f('ix_time_wallet_employee_wallets_user_id'), table_name='employee_wallets', schema='time_wallet')
    op.create_index('ix_wallet_employee_wallets_user_id', 'employee_wallets', ['user_id'], unique=False, schema='time_wallet')
    
    # Remove columns
    op.drop_column('wallet_transactions', 'meta_data', schema='time_wallet')
    op.drop_column('wallet_transactions', 'is_confirmed', schema='time_wallet')
