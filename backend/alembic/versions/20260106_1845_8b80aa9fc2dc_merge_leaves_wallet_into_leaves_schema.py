"""merge_leaves_wallet_into_leaves_schema

Revision ID: 8b80aa9fc2dc
Revises: b7e8d9c0a1b2
Create Date: 2026-01-06 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b80aa9fc2dc'
down_revision: Union[str, None] = 'b7e8d9c0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure leaves schema exists (it should)
    op.execute("CREATE SCHEMA IF NOT EXISTS leaves")

    # 2. Check if tables exist in old schema and move them
    # If this is a fresh install they might not exist, so we use IF EXISTS logic loosely via raw SQL check
    # or just attempt move.
    
    # Move employee_wallets
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'time_wallet' AND table_name = 'employee_wallets') THEN
                ALTER TABLE time_wallet.employee_wallets SET SCHEMA leaves;
            END IF;
        END
        $$;
    """)

    # Move wallet_transactions
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'time_wallet' AND table_name = 'wallet_transactions') THEN
                ALTER TABLE time_wallet.wallet_transactions SET SCHEMA leaves;
            END IF;
        END
        $$;
    """)
    
    # 3. If tables didn't exist in time_wallet (fresh install case where leaves-wallet wasn't deployed or ran),
    # we need to create them in 'leaves'. But Alembic autogenerate usually handles creation.
    # However, since we are merging, we want to ensure they are there.
    # But if we just move them, and they are already tracked by previous migrations?
    # Actually, previous migrations created them in time_wallet.
    # So moving them preserves migration history mostly.
    
    # 4. Clean up old schema if empty? Optional.
    # op.execute("DROP SCHEMA IF EXISTS time_wallet CASCADE") 


def downgrade() -> None:
    # Move back to time_wallet
    op.execute("CREATE SCHEMA IF NOT EXISTS time_wallet")
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'leaves' AND table_name = 'employee_wallets') THEN
                ALTER TABLE leaves.employee_wallets SET SCHEMA time_wallet;
            END IF;
        END
        $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'leaves' AND table_name = 'wallet_transactions') THEN
                ALTER TABLE leaves.wallet_transactions SET SCHEMA time_wallet;
            END IF;
        END
        $$;
    """)
