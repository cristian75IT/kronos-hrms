"""Add email_logs table for enterprise email tracking.

Revision ID: 027_email_logs
Revises: 026_migrate_holidays_closures
Create Date: 2026-01-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '027_email_logs'
down_revision: str = '026_migrate_holidays_closures'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email_logs table for enterprise email tracking."""
    
    # Create email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        
        # Recipient info
        sa.Column('to_email', sa.String(255), nullable=False, index=True),
        sa.Column('to_name', sa.String(200)),
        sa.Column('user_id', UUID(as_uuid=True), index=True),
        
        # Email content
        sa.Column('template_code', sa.String(50), nullable=False, index=True),
        sa.Column('subject', sa.String(300)),
        sa.Column('variables', JSONB),
        
        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, default='pending', index=True),
        # pending, queued, sent, delivered, opened, clicked, bounced, failed
        
        # External IDs
        sa.Column('message_id', sa.String(100), index=True),  # Brevo message ID
        sa.Column('notification_id', UUID(as_uuid=True)),  # Linked notification if any
        
        # Error tracking
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('next_retry_at', sa.DateTime(timezone=True)),
        
        # Provider response
        sa.Column('provider_response', JSONB),
        
        # Tracking events
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('opened_at', sa.DateTime(timezone=True)),
        sa.Column('clicked_at', sa.DateTime(timezone=True)),
        sa.Column('bounced_at', sa.DateTime(timezone=True)),
        sa.Column('failed_at', sa.DateTime(timezone=True)),
        
        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        schema='notifications'
    )
    
    # Create index for filtering by date
    op.create_index(
        'ix_email_logs_created_at',
        'email_logs',
        ['created_at'],
        schema='notifications'
    )
    
    # Add email delivery stats view
    op.execute("""
        CREATE OR REPLACE VIEW notifications.email_delivery_stats AS
        SELECT 
            DATE(created_at) as date,
            template_code,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'sent') as sent,
            COUNT(*) FILTER (WHERE status = 'delivered') as delivered,
            COUNT(*) FILTER (WHERE status = 'opened') as opened,
            COUNT(*) FILTER (WHERE status = 'clicked') as clicked,
            COUNT(*) FILTER (WHERE status = 'bounced') as bounced,
            COUNT(*) FILTER (WHERE status = 'failed') as failed,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE status IN ('sent', 'delivered', 'opened', 'clicked')) / 
                NULLIF(COUNT(*), 0), 
                2
            ) as success_rate
        FROM notifications.email_logs
        GROUP BY DATE(created_at), template_code
        ORDER BY date DESC, template_code;
    """)


def downgrade() -> None:
    """Remove email_logs table."""
    op.execute("DROP VIEW IF EXISTS notifications.email_delivery_stats")
    op.drop_table('email_logs', schema='notifications')
