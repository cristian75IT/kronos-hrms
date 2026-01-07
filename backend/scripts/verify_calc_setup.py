import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.config.models import NationalContractVersion, CalculationMode

async def verify_calc_modes():
    print("🔍 Verifying Calculation Modes on Contract Version...")
    async with get_db_context() as session:
        # Get all versions with this name
        stmt = select(NationalContractVersion).options(
            selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContractVersion.rol_calc_mode)
        ).where(NationalContractVersion.version_name == "Rinnovo 2024-2027")
        
        result = await session.execute(stmt)
        versions = result.scalars().all()
        
        if not versions:
            print("❌ Contract version not found!")
            return
            
        print(f"Found {len(versions)} version(s):")
        for i, version in enumerate(versions):
            print(f"\n📄 Version #{i+1} (ID: {version.id})")
            print(f"   Name: {version.version_name}")
            
            # Check Vacation Mode
            if version.vacation_calc_mode:
                print(f"   ✓ Vacation Mode: {version.vacation_calc_mode.code} ({version.vacation_calc_mode.name})")
                print(f"     Params: {version.vacation_calc_params}")
            else:
                print("   ❌ Vacation Mode: NOT SET")
                
            # Check ROL Mode
            if version.rol_calc_mode:
                print(f"   ✓ ROL Mode: {version.rol_calc_mode.code} ({version.rol_calc_mode.name})")
                print(f"     Params: {version.rol_calc_params}")
            else:
                print("   ❌ ROL Mode: NOT SET")

if __name__ == "__main__":
    asyncio.run(verify_calc_modes())
