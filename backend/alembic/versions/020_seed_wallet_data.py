"""seed_wallet_data

Revision ID: 020_seed_wallet_data
Revises: 019_add_trip_wallets
Create Date: 2026-01-02 09:10:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import date

# revision identifiers, used by Alembic.
revision: str = '020_seed_wallet_data'
down_revision: Union[str, None] = '019_add_trip_wallets'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: Users are synced from Keycloak automatically on first login.
    # Wallet data (employee_wallets) will be created by the leaves_wallet service
    # when users first access the system (on-demand provisioning).
    # This migration only ensures the database schema is ready.
    # No static seed data is inserted here to avoid keycloak_id mismatches.
    pass


def downgrade() -> None:
    # Clean up wallet data if needed
    op.execute("DELETE FROM wallet.trip_wallet_transactions")
    op.execute("DELETE FROM wallet.trip_wallets")
    op.execute("DELETE FROM wallet.wallet_transactions")
    op.execute("DELETE FROM wallet.employee_wallets")
