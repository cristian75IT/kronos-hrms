import asyncio
import sys
import os
from uuid import UUID, uuid4
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.auth.models import User
from src.services.leaves_wallet.models import EmployeeWallet, WalletTransaction
from src.services.expensive_wallet.models import TripWallet
from src.services.hr_reporting.models import HRAlert, DailySnapshot, AlertSeverity

# Fixed UUIDs for consistency
ADMIN_ID = UUID("3a5b855c-e426-42e0-a51a-210fc1ac3f61")
HR_ID = UUID("4b6c966d-f537-53f1-b62b-321fd2bd4372") # Fixed hex digit
STAFF_ID = UUID("5c7d077e-0648-6402-c73c-432ae3ce5a83") # Fixed hex digit

async def seed():
    print("🚀 Starting Enterprise Data Seed...")
    async with get_db_context() as session:
        try:
            # 1. Create/Ensure Users
            # Cristian (Admin/Manager)
            cristian = await session.get(User, ADMIN_ID)
            if not cristian:
                print(f"   👤 Creating Admin: Cristian")
                cristian = User(
                    id=ADMIN_ID,
                    keycloak_id="cristian-kc-id",
                    email="cristian@example.com",
                    username="cristian",
                    first_name="Cristian",
                    last_name="Manager",
                    is_admin=True,
                    is_manager=True,
                    is_active=True
                )
                session.add(cristian)
            
            # Valentina (HR)
            valentina = await session.get(User, HR_ID)
            if not valentina:
                print(f"   👤 Creating HR: Valentina")
                valentina = User(
                    id=HR_ID,
                    keycloak_id="valentina-kc-id",
                    email="valentina@example.com",
                    username="valentina",
                    first_name="Valentina",
                    last_name="HR",
                    is_admin=False,
                    is_manager=True,
                    is_approver=True,
                    is_active=True
                )
                session.add(valentina)

            # Marco (Staff)
            marco = await session.get(User, STAFF_ID)
            if not marco:
                print(f"   👤 Creating Employee: Marco")
                marco = User(
                    id=STAFF_ID,
                    keycloak_id="marco-kc-id",
                    email="marco@example.com",
                    username="marco",
                    first_name="Marco",
                    last_name="Employee",
                    manager_id=ADMIN_ID,
                    is_active=True
                )
                session.add(marco)

            await session.flush()

            # 2. Time Wallets (2025)
            print("   💳 Seeding Time Wallets...")
            for user_id in [ADMIN_ID, STAFF_ID]:
                # Check if exists
                from sqlalchemy import select
                stmt = select(EmployeeWallet).where(EmployeeWallet.user_id == user_id, EmployeeWallet.year == 2025)
                res = await session.execute(stmt)
                wallet = res.scalar()

                if not wallet:
                    wallet = EmployeeWallet(
                        id=uuid4(),
                        user_id=user_id,
                        year=2025,
                        vacation_previous_year=Decimal("5.0"),
                        vacation_accrued=Decimal("26.0"),
                        vacation_used=Decimal("12.0"),
                        vacation_used_ap=Decimal("5.0"),
                        vacation_used_ac=Decimal("7.0"),
                        rol_previous_year=Decimal("8.0"),
                        rol_accrued=Decimal("72.0"),
                        rol_used=Decimal("24.0"),
                        permits_total=Decimal("32.0"),
                        permits_used=Decimal("0.0"),
                        status="ACTIVE",
                        last_accrual_date=date(2025, 12, 31)
                    )
                    session.add(wallet)
                    print(f"      ✓ Wallet 2025 for {user_id}")

            # 3. HR Alerts
            print("   ⚠️ Seeding HR Alerts...")
            alerts = [
                {
                    "title": "Ferie in Scadenza (AP 2024)",
                    "description": "Il dipendente Marco ha 15 giorni di ferie residue del 2024 che scadranno il 30/06/2026.",
                    "severity": "warning",
                    "employee_id": STAFF_ID,
                    "alert_type": "compliance"
                },
                {
                    "title": "Certificato Medico Mancante",
                    "description": "Manca il certificato medico per l'assenza del 02/01/2026 di Marco.",
                    "severity": "critical",
                    "employee_id": STAFF_ID,
                    "alert_type": "missing_document"
                },
                {
                    "title": "Revisione Budget Trasferte",
                    "description": "Il budget per la trasferta 'Progetto X' è quasi esaurito (90%).",
                    "severity": "info",
                    "alert_type": "budget"
                }
            ]

            for a in alerts:
                # Basic check to avoid duplicates in this simple script
                stmt = select(HRAlert).where(HRAlert.title == a["title"])
                res = await session.execute(stmt)
                if not res.scalar():
                    alert = HRAlert(
                        id=uuid4(),
                        title=a["title"],
                        description=a["description"],
                        severity=a["severity"],
                        employee_id=a.get("employee_id"),
                        alert_type=a["alert_type"],
                        is_active=True
                    )
                    session.add(alert)

            # 4. Daily Snapshot (Current Status)
            print("   📊 Seeding HR Daily Snapshot...")
            today = date.today()
            stmt = select(DailySnapshot).where(DailySnapshot.snapshot_date == today)
            res = await session.execute(stmt)
            if not res.scalar():
                snap = DailySnapshot(
                    id=uuid4(),
                    snapshot_date=today,
                    total_employees=3,
                    employees_on_leave=1,
                    employees_on_trip=1,
                    employees_sick=0,
                    absence_rate=Decimal("33.33"),
                    pending_leave_requests=2,
                    pending_expense_reports=3,
                    total_expenses_submitted=Decimal("1250.50")
                )
                session.add(snap)

            # 5. Trip Wallet
            print("   ✈️ Seeding Trip Wallet...")
            TRIP_ID = uuid4()
            stmt = select(TripWallet).where(TripWallet.user_id == STAFF_ID)
            res = await session.execute(stmt)
            if not res.scalar():
                trip_wallet = TripWallet(
                    id=uuid4(),
                    trip_id=TRIP_ID,
                    user_id=STAFF_ID,
                    total_budget=Decimal("2000.00"),
                    total_advances=Decimal("500.00"),
                    total_expenses=Decimal("850.00"),
                    status="OPEN",
                    currency="EUR"
                )
                session.add(trip_wallet)

            await session.commit()
            print("\n✨ Enterprise Seed Completed Successfully!")
            
        except Exception as e:
            print(f"\n❌ Error seeding: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed())
