import asyncio
import sys
import os
from uuid import uuid4

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.config.models import CalculationMode
from sqlalchemy import select

CALC_MODES = [
    {
        "code": "FIXED_RATE",
        "name": "Tasso Fisso Mensile",
        "description": "Maturazione mensile a tasso fisso indipendente dalle ore lavorate",
        "function_name": "accrue_fixed_rate",
        "default_parameters": {"monthly_accrual": 0.0}
    },
    {
        "code": "HOURLY_PRO_RATA",
        "name": "Pro-rata Orario",
        "description": "Maturazione proporzionale alle ore lavorate nel mese",
        "function_name": "accrue_hourly_pro_rata",
        "default_parameters": {"annual_target": 0.0}
    }
]

async def seed_calc_modes():
    print("🚀 Seeding Calculation Modes...")
    async with get_db_context() as session:
        for mode_data in CALC_MODES:
            stmt = select(CalculationMode).where(CalculationMode.code == mode_data["code"])
            res = await session.execute(stmt)
            exists = res.scalar()
            
            if not exists:
                mode = CalculationMode(
                    id=uuid4(),
                    **mode_data
                )
                session.add(mode)
                print(f"   + Created: {mode_data['code']}")
            else:
                print(f"   ✓ Exists: {mode_data['code']}")
        
        await session.commit()
    print("✨ Done.")

if __name__ == "__main__":
    asyncio.run(seed_calc_modes())
