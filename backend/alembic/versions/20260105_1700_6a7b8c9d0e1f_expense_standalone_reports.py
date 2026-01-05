"""Make expense_reports.trip_id nullable and add is_standalone field.

Revision ID: 6a7b8c9d0e1f
Revises: 5c4ec4406a57
Create Date: 2026-01-05 17:00:00.000000

This migration:
1. Makes trip_id nullable in expense_reports (allows standalone reports)
2. Adds is_standalone boolean flag
3. Removes is_approved and rejection_reason from expense_items
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6a7b8c9d0e1f'
down_revision = '5c4ec4406a57'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make trip_id nullable
    op.alter_column(
        'expense_reports',
        'trip_id',
        existing_type=postgresql.UUID(),
        nullable=True,
        schema='expenses'
    )
    
    # Add is_standalone flag
    op.add_column(
        'expense_reports',
        sa.Column('is_standalone', sa.Boolean(), server_default='false', nullable=False),
        schema='expenses'
    )
    
    # Remove approval fields from expense_items
    op.drop_column('expense_items', 'is_approved', schema='expenses')
    op.drop_column('expense_items', 'rejection_reason', schema='expenses')


def downgrade() -> None:
    # Re-add approval fields to expense_items
    op.add_column(
        'expense_items',
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        schema='expenses'
    )
    op.add_column(
        'expense_items',
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        schema='expenses'
    )
    
    # Remove is_standalone flag
    op.drop_column('expense_reports', 'is_standalone', schema='expenses')
    
    # Make trip_id NOT NULL again (will fail if standalone reports exist)
    op.alter_column(
        'expense_reports',
        'trip_id',
        existing_type=postgresql.UUID(),
        nullable=False,
        schema='expenses'
    )
