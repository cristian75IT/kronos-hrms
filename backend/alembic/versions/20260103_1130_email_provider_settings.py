"""Add email_provider_settings table.

Revision ID: 20260103_1130_email_provider_settings
Revises: 20260103_0611_d6ce7d88c30f
Create Date: 2026-01-03 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260103_1130_email_provider'
down_revision: Union[str, None] = 'd6ce7d88c30f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create email_provider_settings table in notifications schema
    op.create_table(
        'email_provider_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False, server_default='brevo'),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column('sender_email', sa.String(255), nullable=False),
        sa.Column('sender_name', sa.String(100), nullable=False, server_default='KRONOS HR'),
        sa.Column('reply_to_email', sa.String(255), nullable=True),
        sa.Column('reply_to_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('test_mode', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('test_email', sa.String(255), nullable=True),
        sa.Column('webhook_secret', sa.String(100), nullable=True),
        sa.Column('daily_limit', sa.Integer(), nullable=True),
        sa.Column('emails_sent_today', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('last_reset_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='notifications'
    )
    
    # Create index for quick lookups
    op.create_index(
        'ix_email_provider_settings_provider_active',
        'email_provider_settings',
        ['provider', 'is_active'],
        schema='notifications'
    )


def downgrade() -> None:
    op.drop_index('ix_email_provider_settings_provider_active', table_name='email_provider_settings', schema='notifications')
    op.drop_table('email_provider_settings', schema='notifications')
