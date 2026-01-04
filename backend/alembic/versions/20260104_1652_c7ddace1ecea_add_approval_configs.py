"""add_approval_configs

Revision ID: c7ddace1ecea
Revises: 065c843d94a9
Create Date: 2026-01-04 16:52:28.543083+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7ddace1ecea'
down_revision: Union[str, None] = '065c843d94a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO config.system_config (id, category, key, value, value_type, description, is_sensitive)
        VALUES 
            (gen_random_uuid(), 'business', 'approval.auto_escalate', 'true', 'boolean', 'Scala automaticamente le approvazioni scadute al livello superiore.', false),
            (gen_random_uuid(), 'email', 'approval.reminder_enabled', 'true', 'boolean', 'Invia promemoria agli approvatori prima della scadenza.', false),
            (gen_random_uuid(), 'business', 'approval.allow_self_approval', 'false', 'boolean', 'Permette agli utenti di approvare le proprie richieste.', false)
        ON CONFLICT (key) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM config.system_config 
        WHERE key IN (
            'approval.auto_escalate', 
            'approval.reminder_enabled', 
            'approval.allow_self_approval'
        )
    """)
