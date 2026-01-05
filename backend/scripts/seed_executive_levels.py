
import asyncio
import logging
import sys
import os

# Add parent directory to path to allow imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory
from src.services.auth.models import ExecutiveLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXECUTIVE_LEVELS = [
    {
        "code": "CEO",
        "title": "Chief Executive Officer",
        "hierarchy_level": 1,
        "can_override_workflow": True,
        "max_approval_amount": None, # Unlimited
        "escalates_to_code": None
    },
    {
        "code": "CIO",
        "title": "Chief Information Officer",
        "hierarchy_level": 2,
        "can_override_workflow": True,
        "max_approval_amount": 50000.00,
        "escalates_to_code": "CEO"
    },
    {
        "code": "CFO",
        "title": "Chief Financial Officer",
        "hierarchy_level": 2,
        "can_override_workflow": True,
        "max_approval_amount": 100000.00,
        "escalates_to_code": "CEO"
    },
    {
        "code": "CHRO",
        "title": "Chief Human Resources Officer",
        "hierarchy_level": 2,
        "can_override_workflow": True,
        "max_approval_amount": 20000.00,
        "escalates_to_code": "CEO"
    },
    {
        "code": "COO",
        "title": "Chief Operating Officer",
        "hierarchy_level": 2,
        "can_override_workflow": True,
        "max_approval_amount": 50000.00,
        "escalates_to_code": "CEO"
    },
    {
        "code": "CCO",
        "title": "Chief Commercial Officer",
        "hierarchy_level": 2,
        "can_override_workflow": True,
        "max_approval_amount": 50000.00,
        "escalates_to_code": "CEO"
    },
    {
        "code": "CRO",
        "title": "Chief Revenue Officer",
        "hierarchy_level": 2,
        "can_override_workflow": True,
        "max_approval_amount": 50000.00,
        "escalates_to_code": "CEO"
    },
]

async def seed_levels():
    async with async_session_factory() as session:
        logger.info("Seeding Executive Levels...")
        
        # 1. Create Levels
        created_levels = {}
        
        for level_data in EXECUTIVE_LEVELS:
            # Check if exists
            query = select(ExecutiveLevel).where(ExecutiveLevel.code == level_data["code"])
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            
            if not existing:
                logger.info(f"Creating {level_data['code']}")
                level = ExecutiveLevel(
                    code=level_data["code"],
                    title=level_data["title"],
                    hierarchy_level=level_data["hierarchy_level"],
                    can_override_workflow=level_data["can_override_workflow"],
                    max_approval_amount=level_data["max_approval_amount"]
                )
                session.add(level)
                await session.flush() # flush to get ID
                created_levels[level.code] = level
            else:
                logger.info(f"Found existing {level_data['code']}")
                created_levels[level_data["code"]] = existing
        
        # 2. Link Escalation
        for level_data in EXECUTIVE_LEVELS:
            escalates_to_code = level_data.get("escalates_to_code")
            if escalates_to_code and escalates_to_code in created_levels:
                level = created_levels[level_data["code"]]
                target = created_levels[escalates_to_code]
                
                # Check if update needed
                if level.escalates_to_id != target.id:
                    level.escalates_to_id = target.id
                    session.add(level)
                    logger.info(f"Linked {level.code} -> {target.code}")
        
        await session.commit()
        logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(seed_levels())
