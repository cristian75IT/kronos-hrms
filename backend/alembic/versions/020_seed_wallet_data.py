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

# Constants for seeding
ADMIN_ID = '00000000-0000-0000-0000-000000000010'
MANAGER_ID = '00000000-0000-0000-0000-000000000011'
EMPLOYEE_ID = '00000000-0000-0000-0000-000000000012'

def upgrade() -> None:
    # 1. Ensure users exist (in case they weren't seeded yet or to ensure IDs)
    # Usually users are synced, but for seeds we want them fixed.
    # Note: Using TRUNCATE or ON CONFLICT might be needed if they exist.
    
    op.execute(f"""
        INSERT INTO auth.users (id, keycloak_id, email, username, first_name, last_name, is_active, is_admin, is_manager, is_approver, is_synced)
        VALUES 
            ('{ADMIN_ID}', 'admin-kc-id', 'admin@kronos.local', 'admin', 'System', 'Administrator', true, true, false, true, true),
            ('{MANAGER_ID}', 'manager-kc-id', 'manager@kronos.local', 'manager', 'Mario', 'Rossi', true, false, true, true, true),
            ('{EMPLOYEE_ID}', 'employee-kc-id', 'employee@kronos.local', 'employee', 'Giuseppe', 'Verdi', true, false, false, false, true)
        ON CONFLICT (email) DO UPDATE SET id = EXCLUDED.id;
    """)

    # 2. Seed Employee Wallets (Leaves)
    wallet_admin_id = '00000000-0000-0000-0000-000000000110'
    wallet_manager_id = '00000000-0000-0000-0000-000000000111'
    wallet_employee_id = '00000000-0000-0000-0000-000000000112'

    op.execute(f"""
        INSERT INTO wallet.employee_wallets 
        (id, user_id, year, 
         vacation_previous_year, vacation_current_year, vacation_accrued, vacation_used, vacation_used_ap, vacation_used_ac,
         rol_previous_year, rol_current_year, rol_accrued, rol_used, 
         permits_total, permits_used, 
         legal_minimum_required, legal_minimum_taken, status)
        VALUES 
            ('{wallet_admin_id}', '{ADMIN_ID}', 2026, 
             10.0, 0.0, 2.16, 0.0, 0.0, 0.0,
             16.0, 0.0, 6.0, 0.0, 
             8.0, 0.0,
             20.0, 0.0, 'ACTIVE'),
            ('{wallet_manager_id}', '{MANAGER_ID}', 2026, 
             5.0, 0.0, 2.16, 0.0, 0.0, 0.0,
             0.0, 0.0, 6.0, 0.0, 
             8.0, 0.0,
             20.0, 0.0, 'ACTIVE'),
            ('{wallet_employee_id}', '{EMPLOYEE_ID}', 2026, 
             0.0, 0.0, 2.16, 0.0, 0.0, 0.0,
             0.0, 0.0, 6.0, 0.0, 
             8.0, 0.0,
             20.0, 0.0, 'ACTIVE')
        ON CONFLICT DO NOTHING;
    """)

    # 3. Add initial transactions (Accruals for Jan 2026)
    op.execute(f"""
        INSERT INTO wallet.wallet_transactions 
        (id, wallet_id, transaction_type, balance_type, amount, balance_after, remaining_amount, category, description, created_at)
        VALUES 
            (gen_random_uuid(), '{wallet_employee_id}', 'accrual', 'vacation_ac', 2.16, 2.16, 2.16, 'ACCRUAL', 'Maturazione Gennaio 2026', '2026-01-01 00:00:00'),
            (gen_random_uuid(), '{wallet_employee_id}', 'accrual', 'rol', 6.0, 6.0, 6.0, 'ACCRUAL', 'Maturazione ROL Gennaio 2026', '2026-01-01 00:00:00'),
            (gen_random_uuid(), '{wallet_employee_id}', 'accrual', 'permits', 8.0, 8.0, 8.0, 'ACCRUAL', 'Maturazione Ex-Festività Gennaio 2026', '2026-01-01 00:00:00')
    """)

    # 4. Seed a Sample Business Trip and its Wallet
    trip_id = '00000000-0000-0000-0000-000000000200'
    op.execute(f"""
        INSERT INTO expenses.business_trips (id, user_id, title, destination, start_date, end_date, status)
        VALUES ('{trip_id}', '{EMPLOYEE_ID}', 'Trasferta Milano - Corso React', 'Milano', '2026-01-15', '2026-01-17', 'APPROVED')
        ON CONFLICT DO NOTHING;
    """)

    trip_wallet_id = '00000000-0000-0000-0000-000000000300'
    op.execute(f"""
        INSERT INTO wallet.trip_wallets (id, trip_id, user_id, total_budget, total_advances, currency, status)
        VALUES ('{trip_wallet_id}', '{trip_id}', '{EMPLOYEE_ID}', 500.00, 100.00, 'EUR', 'OPEN')
        ON CONFLICT DO NOTHING;
    """)

    op.execute(f"""
        INSERT INTO wallet.trip_wallet_transactions (id, wallet_id, transaction_type, amount, category, description)
        VALUES 
            (gen_random_uuid(), '{trip_wallet_id}', 'budget_allocation', 500.00, 'OTHER', 'Budget iniziale trasferta'),
            (gen_random_uuid(), '{trip_wallet_id}', 'advance_payment', 100.00, 'OTHER', 'Anticipo contanti');
    """)

def downgrade() -> None:
    # Just delete from wallet schema as they are safest to remove
    op.execute("DELETE FROM wallet.trip_wallet_transactions")
    op.execute("DELETE FROM wallet.trip_wallets")
    op.execute("DELETE FROM wallet.wallet_transactions")
    op.execute("DELETE FROM wallet.employee_wallets")
