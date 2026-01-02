"""smart_deduction_config

Revision ID: 016_smart_deduction_config
Revises: 4b6b04201f01
Create Date: 2026-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from uuid import uuid4

# revision identifiers, used by Alembic.
revision: str = '016_smart_deduction_config'
down_revision: Union[str, None] = '4b6b04201f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Generiamo un UUID per la configurazione
    config_id = str(uuid4())
    op.execute(
        sa.text(
            f"INSERT INTO config.system_config (id, key, value, value_type, category, description) "
            f"VALUES ('{config_id}', 'smart_deduction_enabled', 'false', 'boolean', 'leaves', "
            f"'Enables automatic prioritisation of leave/ROL deduction based on expiry dates.')"
        )
    )

def downgrade() -> None:
    op.execute(sa.text("DELETE FROM config.system_config WHERE key = 'smart_deduction_enabled'"))
