"""Add enterprise notification features

Revision ID: 025_enterprise_notifications
Revises: 024_add_missing_business_configs
Create Date: 2026-01-02 15:30:00.000000

Adds:
- push_enabled column to user_notification_preferences
- preferences_matrix JSONB column for granular per-type preferences
- push_subscriptions table for Web Push notifications
- alert_before_minutes column to calendar events
- Removes old specific preference columns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = '025_enterprise_notifications'
down_revision = '024_add_missing_business_configs'
branch_labels = None
depends_on = None



def upgrade() -> None:
    # Add new columns to user_notification_preferences
    op.add_column(
        'user_notification_preferences',
        sa.Column('push_enabled', sa.Boolean(), server_default='true', nullable=False),
        schema='notifications'
    )
    op.add_column(
        'user_notification_preferences',
        sa.Column('preferences_matrix', JSONB, server_default='{}', nullable=False),
        schema='notifications'
    )
    
    # Drop old specific email preference columns
    op.drop_column('user_notification_preferences', 'email_leave_updates', schema='notifications')
    op.drop_column('user_notification_preferences', 'email_expense_updates', schema='notifications')
    op.drop_column('user_notification_preferences', 'email_system_announcements', schema='notifications')
    op.drop_column('user_notification_preferences', 'email_compliance_alerts', schema='notifications')
    
    # Create push_subscriptions table
    op.create_table(
        'push_subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh', sa.String(200), nullable=False),
        sa.Column('auth', sa.String(100), nullable=False),
        sa.Column('device_info', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='notifications'
    )
    
    # Add index on endpoint for upsert operations
    op.create_index(
        'ix_push_subscriptions_endpoint',
        'push_subscriptions',
        ['endpoint'],
        schema='notifications'
    )
    
    # Add alert_before_minutes to calendar events (default 48 hours = 2880 minutes)
    op.add_column(
        'events',
        sa.Column('alert_before_minutes', sa.Integer(), server_default='2880', nullable=True),
        schema='calendar'
    )


def downgrade() -> None:
    # Drop alert_before_minutes from calendar events
    op.drop_column('events', 'alert_before_minutes', schema='calendar')
    
    # Drop push_subscriptions table
    op.drop_index('ix_push_subscriptions_endpoint', table_name='push_subscriptions', schema='notifications')
    op.drop_table('push_subscriptions', schema='notifications')
    
    # Remove new columns
    op.drop_column('user_notification_preferences', 'preferences_matrix', schema='notifications')
    op.drop_column('user_notification_preferences', 'push_enabled', schema='notifications')

    
    # Restore old columns
    op.add_column(
        'user_notification_preferences',
        sa.Column('email_leave_updates', sa.Boolean(), server_default='true', nullable=False),
        schema='notifications'
    )
    op.add_column(
        'user_notification_preferences',
        sa.Column('email_expense_updates', sa.Boolean(), server_default='true', nullable=False),
        schema='notifications'
    )
    op.add_column(
        'user_notification_preferences',
        sa.Column('email_system_announcements', sa.Boolean(), server_default='true', nullable=False),
        schema='notifications'
    )
    op.add_column(
        'user_notification_preferences',
        sa.Column('email_compliance_alerts', sa.Boolean(), server_default='true', nullable=False),
        schema='notifications'
    )
