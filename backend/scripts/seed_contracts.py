import asyncio
import sys
import os
from uuid import UUID, uuid4
from datetime import date, timedelta
from decimal import Decimal

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from src.core.database import get_db_context
from src.services.auth.models import User, EmployeeContract
from src.services.config.models import (
    NationalContract, NationalContractVersion, NationalContractLevel, 
    ContractType, NationalContractTypeConfig
)

# Fixed UUIDs matching seed_enterprise_data.py
ADMIN_ID = UUID("3a5b855c-e426-42e0-a51a-210fc1ac3f61")
HR_ID = UUID("4b6c966d-f537-53f1-b62b-321fd2bd4372")
STAFF_ID = UUID("5c7d077e-0648-6402-c73c-432ae3ce5a83")

EMPLOYEES = [ADMIN_ID, HR_ID, STAFF_ID]

async def seed_contracts():
    print("🚀 Starting Contracts Seed...")
    async with get_db_context() as session:
        try:
            # 1. Seed National Contract (CCNL Commercio)
            print("   📜 Seeding CCNL Commercio...")
            stmt = select(NationalContract).where(NationalContract.code == "COMMERCIO")
            res = await session.execute(stmt)
            ccnl = res.scalar()
            
            if not ccnl:
                ccnl = NationalContract(
                    id=uuid4(),
                    code="COMMERCIO",
                    name="CCNL Commercio - Terziario, Distribuzione e Servizi",
                    sector="Terziario",
                    description="Contratto Collettivo Nazionale di Lavoro per i dipendenti da aziende del terziario della distribuzione e dei servizi.",
                    source_url="https://www.confcommercio.it"
                )
                session.add(ccnl)
                await session.flush()
                print("      + Created CCNL Commercio")
            else:
                print("      ✓ CCNL Commercio exists")
            
            # 2. Seed Levels for Commercio
            levels_data = [
                ("Q", "Quadro", 1),
                ("1", "I Livello", 2),
                ("2", "II Livello", 3),
                ("3", "III Livello", 4),
                ("4", "IV Livello", 5),
                ("5", "V Livello", 6),
                ("6", "VI Livello", 7),
                ("7", "VII Livello", 8)
            ]
            
            level_map = {} # code -> level object
            
            print("   📊 Seeding Contract Levels...")
            for code, name, order in levels_data:
                stmt = select(NationalContractLevel).where(
                    NationalContractLevel.national_contract_id == ccnl.id,
                    NationalContractLevel.level_name == name # Using name as unique identifier within contract for this seed
                )
                res = await session.execute(stmt)
                level = res.scalar()
                
                if not level:
                    level = NationalContractLevel(
                        id=uuid4(),
                        national_contract_id=ccnl.id,
                        level_name=name,
                        description=f"Livello {code} del CCNL Commercio",
                        sort_order=order
                    )
                    session.add(level)
                    print(f"      + Created Level {name}")
                else:
                    # Update sort order if needed
                    level.sort_order = order
                    
                level_map[code] = level
            
            await session.flush()
            
            # 3. Seed Contract Version (Rinnovo 2024)
            print("   📅 Seeding Contract Version (2024)...")
            stmt = select(NationalContractVersion).where(
                NationalContractVersion.national_contract_id == ccnl.id,
                NationalContractVersion.version_name == "Rinnovo 2024-2027"
            )
            res = await session.execute(stmt)
            version = res.scalar()
            
            if not version:
                version = NationalContractVersion(
                    id=uuid4(),
                    national_contract_id=ccnl.id,
                    version_name="Rinnovo 2024-2027",
                    valid_from=date(2024, 3, 1),
                    valid_to=date(2027, 2, 28),
                    weekly_hours_full_time=40.0,
                    working_days_per_week=5,
                    daily_hours=8.0,
                    annual_vacation_days=26,
                    annual_rol_hours=72,
                    annual_ex_festivita_hours=32,
                    vacation_accrual_method="monthly",
                    rol_accrual_method="monthly",
                    sick_leave_carenza_days=3,
                    sick_leave_max_days_year=180,
                    notes="Rinnovo CCNL Commercio marco 2024"
                )
                session.add(version)
                await session.flush()
                print("      + Created Version 2024-2027")
            else:
                print("      ✓ Version 2024-2027 exists")
                
            # 4. Seed Contract Types (Full Time / Part Time)
            print("   📋 Seeding Contract Types...")
            types_data = [
                ("FT", "Full Time", False, 100.0),
                ("PT50", "Part Time 50%", True, 50.0),
                ("PT75", "Part Time 75%", True, 75.0)
            ]
            
            type_map = {}
            
            for code, name, is_pt, pt_pct in types_data:
                stmt = select(ContractType).where(ContractType.code == code)
                res = await session.execute(stmt)
                ctype = res.scalar()
                
                if not ctype:
                    ctype = ContractType(
                        id=uuid4(),
                        code=code,
                        name=name,
                        description=name,
                        is_part_time=is_pt,
                        part_time_percentage=pt_pct,
                        annual_vacation_days=26, # Default fallback
                        annual_rol_hours=int(72 * (pt_pct/100)), # Pro-rated default
                        annual_permit_hours=0
                    )
                    session.add(ctype)
                    print(f"      + Created Type {name}")
                
                type_map[code] = ctype
                
            await session.flush()
            
            # 5. Link Types to Version (ContractConfig)
            print("   🔗 Linking Types to Version...")
            for code, ctype in type_map.items():
                stmt = select(NationalContractTypeConfig).where(
                    NationalContractTypeConfig.national_contract_version_id == version.id,
                    NationalContractTypeConfig.contract_type_id == ctype.id
                )
                res = await session.execute(stmt)
                config = res.scalar()
                
                if not config:
                    # Calculate pro-rated values
                    pct = ctype.part_time_percentage / 100.0
                    hours = 40.0 * pct
                    rol = int(72 * pct)
                    ex_fest = int(32 * pct) # Usually pro-rated
                    
                    config = NationalContractTypeConfig(
                        id=uuid4(),
                        national_contract_version_id=version.id,
                        contract_type_id=ctype.id,
                        weekly_hours=hours,
                        annual_vacation_days=26, # Vacation days usually remain 26 even for PT vertical, but hours change. Keeping simplistic for now.
                        annual_rol_hours=rol,
                        annual_ex_festivita_hours=ex_fest,
                        description=f"Configurazione {ctype.name}"
                    )
                    session.add(config)
                    print(f"      + Linked {ctype.name} to Version")
            
            await session.flush()
            
            # 6. Assign Contracts to Users
            print("   👥 Assigning Contracts to Users...")
            import json # Ensure json is imported
            
            # Admin: Quadro, Full Time
            stmt = select(EmployeeContract).where(EmployeeContract.user_id == ADMIN_ID)
            if not (await session.execute(stmt)).scalar():
                c_admin = EmployeeContract(
                    id=uuid4(),
                    user_id=ADMIN_ID,
                    contract_type_id=type_map["FT"].id,
                    national_contract_id=ccnl.id,
                    level_id=level_map["Q"].id,
                    start_date=date(2020, 1, 1),
                    weekly_hours=40,
                    job_title="IT Manager",
                    department="IT",
                    wage_data=json.dumps({"gross_annual": 50000, "superminimo": 2000})
                )
                session.add(c_admin)
                print("      + Contract for Cristian (Admin)")
                
            # HR: 1 Livello, Full Time
            stmt = select(EmployeeContract).where(EmployeeContract.user_id == HR_ID)
            if not (await session.execute(stmt)).scalar():
                c_hr = EmployeeContract(
                    id=uuid4(),
                    user_id=HR_ID,
                    contract_type_id=type_map["FT"].id,
                    national_contract_id=ccnl.id,
                    level_id=level_map["1"].id,
                    start_date=date(2021, 5, 1),
                    weekly_hours=40,
                    job_title="HR Manager",
                    department="HR",
                    wage_data=json.dumps({"gross_annual": 42000})
                )
                session.add(c_hr)
                print("      + Contract for Valentina (HR)")

            # Staff: 3 Livello, Part Time 75%
            stmt = select(EmployeeContract).where(EmployeeContract.user_id == STAFF_ID)
            if not (await session.execute(stmt)).scalar():
                c_staff = EmployeeContract(
                    id=uuid4(),
                    user_id=STAFF_ID,
                    contract_type_id=type_map["PT75"].id,
                    national_contract_id=ccnl.id,
                    level_id=level_map["3"].id,
                    start_date=date(2023, 1, 10),
                    weekly_hours=30,
                    job_title="Software Developer",
                    department="IT",
                    wage_data=json.dumps({"gross_annual": 28000})
                )
                session.add(c_staff)
                print("      + Contract for Marco (Staff)")

            await session.commit()
            print("\n✨ Contracts Seed Completed Successfully!")
            
        except Exception as e:
            print(f"\n❌ Error seeding Contracts: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_contracts())
