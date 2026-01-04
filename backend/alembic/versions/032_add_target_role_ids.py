"""Add target_role_ids to workflow_configs

Revision ID: 032_add_target_role_ids
Revises: 006_approvals_schema
Create Date: 2026-01-04

Adds target_role_ids column to workflow_configs for role-based workflow assignment.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '032_add_target_role_ids'
down_revision = '006_approvals_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add target_role_ids column to workflow_configs
    op.add_column(
        'workflow_configs',
        sa.Column('target_role_ids', postgresql.JSONB, nullable=True, server_default='[]'),
        schema='approvals'
    )


def downgrade() -> None:
    op.drop_column('workflow_configs', 'target_role_ids', schema='approvals')
