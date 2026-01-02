"""seed_generic_email_templates

Revision ID: seed_generic_tmpl
Revises: b49418a1226b
Create Date: 2026-01-02 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'seed_generic_tmpl'
down_revision = '027_email_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert generic template
    op.execute("""
        INSERT INTO notifications.email_templates (id, code, notification_type, name, subject, html_content, text_content, is_active)
        VALUES 
            (gen_random_uuid(), 'generic_notification', 'system_announcement', 'Notifica Generica', 
             '{{title}}',
             '<div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2 style="color: #2563eb;">{{title}}</h2>
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb;">
                    <p style="margin: 0; font-size: 16px;">{{message}}</p>
                </div>
                {{#if action_url}}
                <div style="margin-top: 20px;">
                    <a href="{{action_url}}" style="display: inline-block; background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Vai all''applicazione</a>
                </div>
                {{/if}}
                <p style="margin-top: 30px; font-size: 12px; color: #666;">
                    Questa è una notifica automatica da KRONOS.
                </p>
             </div>',
             '{{title}}\n\n{{message}}\n\n{{#if action_url}}Link: {{action_url}}{{/if}}',
             true)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM notifications.email_templates WHERE code = 'generic_notification'")
