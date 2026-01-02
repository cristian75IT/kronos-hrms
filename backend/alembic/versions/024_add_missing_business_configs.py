"""Add missing business and notification configurations.

Revision ID: 024_add_missing_business_configs
Revises: b49418a1226b
Create Date: 2026-01-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = '024_add_missing_business_configs'
down_revision = '023_add_calendar_sharing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO config.system_config (id, category, key, value, value_type, description, is_sensitive)
        VALUES 
            (gen_random_uuid(), 'leaves', 'leaves.block_insufficient_balance', 'true', 'boolean', 'Impedisce l''invio di richieste se il saldo disponibile non è sufficiente.', false),
            (gen_random_uuid(), 'notifications', 'notify_leave_request', 'true', 'boolean', 'Invia email ai responsabili quando un dipendente richiede ferie.', false),
            (gen_random_uuid(), 'notifications', 'notify_leave_approval', 'true', 'boolean', 'Notifica il dipendente quando la sua richiesta viene approvata o rifiutata.', false),
            (gen_random_uuid(), 'notifications', 'notify_wallet_expiry', 'false', 'boolean', 'Avvisa i dipendenti un mese prima della scadenza delle ferie AP.', false),
            (gen_random_uuid(), 'notifications', 'push_approvals', 'true', 'boolean', 'Abilita notifiche push per gli approvatori.', false)
        ON CONFLICT (key) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM config.system_config 
        WHERE key IN (
            'leaves.block_insufficient_balance', 
            'notify_leave_request', 
            'notify_leave_approval', 
            'notify_wallet_expiry', 
            'push_approvals'
        )
    """)
