"""add max_single_request_days to leave_types

Revision ID: 20260107_max_days
Revises: c3d4e5f6g7h8
Create Date: 2026-01-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260107_max_days'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'leave_types',
        sa.Column('max_single_request_days', sa.Integer(), nullable=True),
        schema='config'
    )


def downgrade() -> None:
    op.drop_column('leave_types', 'max_single_request_days', schema='config')
