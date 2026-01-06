"""merge_expensive_wallet_into_expenses_schema

Revision ID: c3d4e5f6g7h8
Revises: 8b80aa9fc2dc
Create Date: 2026-01-06 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = '8b80aa9fc2dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure expenses schema exists (it should)
    op.execute("CREATE SCHEMA IF NOT EXISTS expenses")

    # 2. Move trip_wallets
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'wallet' AND table_name = 'trip_wallets') THEN
                ALTER TABLE wallet.trip_wallets SET SCHEMA expenses;
            END IF;
        END
        $$;
    """)

    # 3. Move trip_wallet_transactions
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'wallet' AND table_name = 'trip_wallet_transactions') THEN
                ALTER TABLE wallet.trip_wallet_transactions SET SCHEMA expenses;
            END IF;
        END
        $$;
    """)
    
    # 4. Update Foreign Keys if they were hardcoded with 'wallet' schema
    # PostgreSQL ALter Table Set Schema handles internal FKs usually, 
    # but let's be explicit if needed. 
    # Actually, SQLAlchemy models now point to 'expenses.trip_wallets.id'.

def downgrade() -> None:
    # Move back to wallet
    op.execute("CREATE SCHEMA IF NOT EXISTS wallet")
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'expenses' AND table_name = 'trip_wallets') THEN
                ALTER TABLE expenses.trip_wallets SET SCHEMA wallet;
            END IF;
        END
        $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'expenses' AND table_name = 'trip_wallet_transactions') THEN
                ALTER TABLE expenses.trip_wallet_transactions SET SCHEMA wallet;
            END IF;
        END
        $$;
    """)
