"""add_recall_columns

Revision ID: 018_add_recall_columns
Revises: 017_fix_balance_tx_reason
Create Date: 2026-01-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '018_add_recall_columns'
down_revision: Union[str, None] = '017_fix_balance_tx_reason'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add days_used_before_recall column
    op.add_column('leave_requests', 
                  sa.Column('days_used_before_recall', sa.Numeric(5, 2), nullable=True), 
                  schema='leaves')
    
    # Add recall_date column
    op.add_column('leave_requests', 
                  sa.Column('recall_date', sa.Date(), nullable=True), 
                  schema='leaves')

def downgrade() -> None:
    op.drop_column('leave_requests', 'recall_date', schema='leaves')
    op.drop_column('leave_requests', 'days_used_before_recall', schema='leaves')
