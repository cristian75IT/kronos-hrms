"""Add more notification settings to system_config

Revision ID: 012_notification_settings
Revises: 011_balance_tx_remaining
Create Date: 2024-01-01 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_notification_settings'
down_revision = '011_balance_tx_remaining'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO config.system_config (id, category, key, value, value_type, description, is_sensitive)
        VALUES 
            (gen_random_uuid(), 'notifications', 'notify_manager_on_request', 'true', 'boolean', 'Invia email al responsabile su nuova richiesta', false),
            (gen_random_uuid(), 'notifications', 'notify_user_on_status_change', 'true', 'boolean', 'Invia email al dipendente su cambio stato richiesta', false),
            (gen_random_uuid(), 'notifications', 'notify_on_expiry_warning', 'true', 'boolean', 'Invia reminder prima della scadenza ferie/ROL', false),
            (gen_random_uuid(), 'notifications', 'notify_admin_on_accrual_complete', 'true', 'boolean', 'Notifica amministratori al termine dei ratei mensili', false)
        ON CONFLICT (key) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM config.system_config 
        WHERE key IN (
            'notify_manager_on_request', 
            'notify_user_on_status_change', 
            'notify_on_expiry_warning', 
            'notify_admin_on_accrual_complete'
        )
    """)
