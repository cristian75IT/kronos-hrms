import asyncio
import sys
import os
from uuid import UUID, uuid4
from datetime import date, timedelta
from decimal import Decimal
import random
import json

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from src.core.database import get_db_context
from src.services.expenses.models import BusinessTrip, ExpenseReport, ExpenseItem, TripStatus, ExpenseReportStatus
from src.services.config.models import ExpenseType

# Fixed UUIDs matching seed_enterprise_data.py
ADMIN_ID = UUID("3a5b855c-e426-42e0-a51a-210fc1ac3f61")
HR_ID = UUID("4b6c966d-f537-53f1-b62b-321fd2bd4372")
STAFF_ID = UUID("5c7d077e-0648-6402-c73c-432ae3ce5a83")

async def seed_trips_expenses():
    print("🚀 Starting Trips & Expenses Seed...")
    async with get_db_context() as session:
        try:
            # 1. Seed Expense Types (if not exist)
            print("   💸 Seeding Expense Types...")
            exp_types = [
                ("HOTEL", "Hotel & Alloggio", "lodging"),
                ("TRENO", "Biglietto Treno", "transport"),
                ("AEREO", "Biglietto Aereo", "transport"),
                ("TAXI", "Taxi / Uber", "transport"),
                ("PASTO", "Pasto / Ristorante", "meals"),
                ("AUTO", "Rimborso Km Auto", "transport"),
                ("ALTRO", "Altro", "other")
            ]
            
            type_map = {} # code -> id
            
            for code, name, cat in exp_types:
                stmt = select(ExpenseType).where(ExpenseType.code == code)
                res = await session.execute(stmt)
                et = res.scalar()
                
                if not et:
                    et = ExpenseType(
                        id=uuid4(),
                        code=code,
                        name=name,
                        category=cat,
                        requires_receipt=True,
                        is_active=True
                    )
                    session.add(et)
                    print(f"      + Created Type {name}")
                
                type_map[code] = et.id
                
            await session.flush()
            
            # 2. Create Trips for Staff (Marco)
            print("   ✈️ Seeding Trips for Marco...")
            
            # Trip 1: Completed last month
            trip1_id = uuid4()
            start_date1 = date.today() - timedelta(days=40)
            end_date1 = start_date1 + timedelta(days=2) # 3 days. Total days = 3.
            
            stmt = select(BusinessTrip).where(
                BusinessTrip.user_id == STAFF_ID, 
                BusinessTrip.destination == "Milano - Cliente Alpha"
            )
            if not (await session.execute(stmt)).scalar():
                trip1 = BusinessTrip(
                    id=trip1_id,
                    user_id=STAFF_ID,
                    title="Workshop Milano",
                    destination="Milano - Cliente Alpha",
                    purpose="Incontro progetto e workshop",
                    start_date=start_date1,
                    end_date=end_date1,
                    estimated_budget=Decimal("500.00"),
                    status=TripStatus.COMPLETED,
                    description="Trasferta conclusa con successo."
                )
                session.add(trip1)
                print(f"      + Created Completed Trip to Milano")
                
                # Create Expense Report associated with Trip 1
                report1 = ExpenseReport(
                    id=uuid4(),
                    user_id=STAFF_ID,
                    trip_id=trip1_id,
                    title=f"Spese Milano {start_date1.strftime('%d/%m')}",
                    employee_notes="Spese vitto e alloggio trasferta Milano",
                    status=ExpenseReportStatus.SUBMITTED,
                    total_amount=Decimal("350.50"),
                    report_number=f"EXP-{date.today().year}-0001",
                    period_start=start_date1,
                    period_end=end_date1,
                )
                session.add(report1)
                
                # Items for Report 1
                items1 = [
                    ("TRENO", 85.00, start_date1, "Treno Andata"),
                    ("TRENO", 85.00, end_date1, "Treno Ritorno"),
                    ("HOTEL", 120.00, start_date1, "Hotel 2 notti"),
                    ("PASTO", 35.50, start_date1, "Cena con cliente"),
                    ("TAXI", 25.00, end_date1, "Taxi Stazione-Ufficio")
                ]
                
                for code, amt, d, desc in items1:
                    tid = type_map[code]
                    item = ExpenseItem(
                        id=uuid4(),
                        report_id=report1.id,
                        expense_type_id=tid,
                        expense_type_code=code,
                        amount=Decimal(str(amt)),
                        amount_eur=Decimal(str(amt)),
                        date=d,
                        description=desc,
                        currency="EUR"
                    )
                    session.add(item)
                
            # Trip 2: Planned Next Month
            start_date2 = date.today() + timedelta(days=20)
            end_date2 = start_date2 + timedelta(days=4)
            
            stmt = select(BusinessTrip).where(
                BusinessTrip.user_id == STAFF_ID, 
                BusinessTrip.destination == "Roma - Conferenza Tech"
            )
            if not (await session.execute(stmt)).scalar():
                trip2 = BusinessTrip(
                    id=uuid4(),
                    user_id=STAFF_ID,
                    title="Conferenza Tech Roma",
                    destination="Roma - Conferenza Tech",
                    purpose="Aggiornamento professionale",
                    start_date=start_date2,
                    end_date=end_date2,
                    estimated_budget=Decimal("1200.00"),
                    status=TripStatus.APPROVED
                )
                session.add(trip2)
                print(f"      + Created Planned Trip to Roma")
            
            # 3. Standalone Expenses (No Trip) for Admin
            print("   🧾 Seeding Expenses for Admin...")
            stmt = select(ExpenseReport).where(
                ExpenseReport.user_id == ADMIN_ID,
                ExpenseReport.title == "Acquisti Hardware Minori"
            )
            if not (await session.execute(stmt)).scalar():
                report2 = ExpenseReport(
                    id=uuid4(),
                    user_id=ADMIN_ID,
                    title="Acquisti Hardware Minori",
                    employee_notes="Mouse e tastiere per nuovi stagisti",
                    status=ExpenseReportStatus.APPROVED,
                    total_amount=Decimal("150.99"),
                    report_number=f"EXP-{date.today().year}-0002",
                    period_start=date.today() - timedelta(days=6),
                    period_end=date.today() - timedelta(days=5),
                    approved_at=date.today() - timedelta(days=1), # Changed from approval_date
                    approved_amount=Decimal("150.99"),
                    is_standalone=True
                )
                session.add(report2)
                
                item2 = ExpenseItem(
                    id=uuid4(),
                    report_id=report2.id,
                    expense_type_id=type_map["ALTRO"],
                    expense_type_code="ALTRO",
                    amount=Decimal("150.99"),
                    amount_eur=Decimal("150.99"),
                    date=date.today() - timedelta(days=6),
                    description="Kit periferiche Logitech",
                    currency="EUR"
                )
                session.add(item2)
                print(f"      + Created Standalone Expense Report")

            await session.commit()
            print("\n✨ Trips & Expenses Seed Completed Successfully!")
            
        except Exception as e:
            print(f"\n❌ Error seeding Trips & Expenses: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_trips_expenses())
