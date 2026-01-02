"""fix_balance_tx_reason

Revision ID: 017_fix_balance_tx_reason
Revises: 016_smart_deduction_config
Create Date: 2026-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '017_fix_balance_tx_reason'
down_revision: Union[str, None] = '016_smart_deduction_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Rename column description to reason in leaves.balance_transactions
    op.alter_column('balance_transactions', 'description', new_column_name='reason', schema='leaves')
    
    # Adjust amount precision to match model
    op.alter_column('balance_transactions', 'amount', 
                    type_=sa.Numeric(6, 2), 
                    existing_type=sa.Numeric(5, 2),
                    schema='leaves')

def downgrade() -> None:
    op.alter_column('balance_transactions', 'reason', new_column_name='description', schema='leaves')
    op.alter_column('balance_transactions', 'amount', 
                    type_=sa.Numeric(5, 2), 
                    existing_type=sa.Numeric(6, 2),
                    schema='leaves')
