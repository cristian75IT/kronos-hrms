
import asyncio
import logging
import sys
import os
from uuid import UUID

# Add parent directory to path to allow imports from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select
from src.core.database import async_session_factory
from src.services.auth.models import User, Department, OrganizationalService, ExecutiveLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User IDs from seed_enterprise_data.py
ADMIN_ID = UUID("3a5b855c-e426-42e0-a51a-210fc1ac3f61")   # Cristian
HR_ID = UUID("4b6c966d-f537-53f1-b62b-321fd2bd4372")      # Valentina
STAFF_ID = UUID("5c7d077e-0648-6402-c73c-432ae3ce5a83")   # Marco

async def seed_organization():
    async with async_session_factory() as session:
        logger.info("🚀 Seeding Organization Structure...")

        # 1. Fetch Users
        cristian = await session.get(User, ADMIN_ID)
        valentina = await session.get(User, HR_ID)
        marco = await session.get(User, STAFF_ID)

        if not cristian or not valentina or not marco:
            logger.error("❌ Core users not found! Run seed_enterprise_data.py first.")
            return

        # 2. Fetch Executive Levels (Assumes seed_executive_levels.py has run)
        stmt = select(ExecutiveLevel)
        result = await session.execute(stmt)
        levels = {l.code: l for l in result.scalars().all()}
        
        if not levels:
            logger.error("❌ Executive levels not found! Run seed_executive_levels.py first.")
            return

        # 3. Assign Executive Levels
        logger.info("👑 Assigning Executive Levels...")
        if "CIO" in levels:
            cristian.executive_level_id = levels["CIO"].id
            logger.info(f"   Assigning CIO to {cristian.full_name}")
        
        if "CHRO" in levels:
            valentina.executive_level_id = levels["CHRO"].id
            logger.info(f"   Assigning CHRO to {valentina.full_name}")

        session.add(cristian)
        session.add(valentina)
        await session.flush()

        # 4. Create Departments
        logger.info("🏢 Creating Departments...")
        departments = {}
        
        dept_data = [
            {"code": "IT", "name": "Information Technology", "manager_id": cristian.id},
            {"code": "HR", "name": "Human Resources", "manager_id": valentina.id},
            {"code": "FIN", "name": "Finance", "manager_id": None},
            {"code": "SALES", "name": "Sales & Marketing", "manager_id": None},
        ]

        for d in dept_data:
            stmt = select(Department).where(Department.code == d["code"])
            res = await session.execute(stmt)
            dept = res.scalar_one_or_none()

            if not dept:
                dept = Department(
                    code=d["code"],
                    name=d["name"],
                    manager_id=d["manager_id"],
                    hierarchy_level=2,
                    is_active=True
                )
                session.add(dept)
                await session.flush()
                logger.info(f"   Created Department: {d['name']}")
            else:
                dept.manager_id = d["manager_id"]
                session.add(dept)
                logger.info(f"   Updated Department: {d['name']}")
            
            departments[d["code"]] = dept

        # 5. Create Services
        logger.info("🛠️ Creating Services...")
        services = {}
        
        svc_data = [
            {"code": "DEV", "name": "Software Development", "dept_code": "IT", "coordinator_id": cristian.id},
            {"code": "OPS", "name": "DevOps & Infra", "dept_code": "IT", "coordinator_id": None},
            {"code": "TA", "name": "Talent Acquisition", "dept_code": "HR", "coordinator_id": None},
            {"code": "ADMIN", "name": "HR Administration", "dept_code": "HR", "coordinator_id": None},
        ]

        for s in svc_data:
            dept = departments.get(s["dept_code"])
            if not dept:
                continue

            stmt = select(OrganizationalService).where(OrganizationalService.code == s["code"])
            res = await session.execute(stmt)
            svc = res.scalar_one_or_none()

            if not svc:
                svc = OrganizationalService(
                    code=s["code"],
                    name=s["name"],
                    department_id=dept.id,
                    coordinator_id=s["coordinator_id"],
                    description=f"Service for {dept.name}"
                )
                session.add(svc)
                await session.flush()
                logger.info(f"   Created Service: {s['name']} (under {dept.code})")
            else:
                svc.coordinator_id = s["coordinator_id"]
                session.add(svc)
            
            services[s["code"]] = svc

        # 6. Assign Users to Org Structure
        logger.info("👥 Assigning Users to Structure...")
        
        # Cristian -> IT Dept (Manager)
        cristian.department_id = departments["IT"].id
        cristian.service_id = services["DEV"].id
        
        # Valentina -> HR Dept (Manager)
        valentina.department_id = departments["HR"].id
        valentina.service_id = services["ADMIN"].id
        
        # Marco -> IT Dept / Dev Service
        if marco:
            marco.department_id = departments["IT"].id
            marco.service_id = services["DEV"].id
            logger.info(f"   Assigned {marco.full_name} to IT / Software Development")

        session.add(cristian)
        session.add(valentina)
        session.add(marco)
        
        await session.commit()
        logger.info("✅ Organization Seeding Complete.")

if __name__ == "__main__":
    asyncio.run(seed_organization())
