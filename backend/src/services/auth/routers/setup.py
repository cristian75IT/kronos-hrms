from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload
from src.services.auth.service import OrganizationService, UserService
from src.services.auth.schemas import (
    SetupExecutiveLevelsPayload,
    SetupOrganizationPayload,
    SetupUsersPayload,
    ExecutiveLevelCreate,
    ExecutiveLevelUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    OrganizationalServiceCreate,
    OrganizationalServiceUpdate,
    UserCreate,
    UserUpdate
)
from src.services.auth.models import ExecutiveLevel, Department, OrganizationalService

router = APIRouter()

async def get_org_service(session: AsyncSession = Depends(get_db)):
    return OrganizationService(session)

async def get_user_service(session: AsyncSession = Depends(get_db)):
    return UserService(session)

@router.post("/setup/executive-levels", response_model=dict)
async def setup_executive_levels(
    payload: SetupExecutiveLevelsPayload,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    org_service: OrganizationService = Depends(get_org_service)
):
    """Bulk setup executive levels."""
    results = {"created": 0, "updated": 0}
    
    # First pass: Create or Update levels without linking escalation yet
    for level_data in payload.levels:
        existing = await org_service._dept_repo._session.execute(
            select(ExecutiveLevel).where(ExecutiveLevel.code == level_data.code)
        )
        level = existing.scalar_one_or_none()
        
        if level:
            # Prepare update - use fields from Setup schema
            update_data = ExecutiveLevelUpdate(
                title=level_data.title,
                hierarchy_level=level_data.hierarchy_level,
                max_approval_amount=level_data.max_approval_amount,
                can_override_workflow=level_data.can_override_workflow
            )
            await org_service.update_executive_level(
                level.id,
                update_data,
                actor_id=token.user_id
            )
            results["updated"] += 1
        else:
            # Create
            create_data = ExecutiveLevelCreate(
                code=level_data.code,
                title=level_data.title,
                hierarchy_level=level_data.hierarchy_level,
                max_approval_amount=level_data.max_approval_amount,
                can_override_workflow=level_data.can_override_workflow
            )
            await org_service.create_executive_level(
                create_data,
                actor_id=token.user_id
            )
            results["created"] += 1
            
    # Second pass: Link escalation
    for level_data in payload.levels:
        if level_data.escalates_to_code:
            # Find level by code
            level_res = await org_service._dept_repo._session.execute(
                select(ExecutiveLevel).where(ExecutiveLevel.code == level_data.code)
            )
            level = level_res.scalar_one_or_none()
            
            target_res = await org_service._dept_repo._session.execute(
                select(ExecutiveLevel).where(ExecutiveLevel.code == level_data.escalates_to_code)
            )
            target = target_res.scalar_one_or_none()
            
            if level and target:
                await org_service.update_executive_level(
                    level.id,
                    ExecutiveLevelUpdate(escalates_to_id=target.id),
                    actor_id=token.user_id
                )
    
    return results

@router.post("/setup/organization", response_model=dict)
async def setup_organization(
    payload: SetupOrganizationPayload,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    org_service: OrganizationService = Depends(get_org_service),
    user_service: UserService = Depends(get_user_service)
):
    """Bulk setup organization structure (Departments and Services)."""
    results = {"departments": 0, "services": 0}
    
    for dept_data in payload.departments:
        # 1. Handle Department
        existing_dept = await org_service._dept_repo.get_by_code(dept_data.code)
        
        manager_id = None
        if dept_data.manager_email:
            user = await user_service._user_repo.get_by_email(dept_data.manager_email)
            if user:
                manager_id = user.id
                
        dept_id = None
        if existing_dept:
            dept_id = existing_dept.id
            # Update
            await org_service.update_department(
                dept_id,
                DepartmentUpdate(
                    name=dept_data.name,
                    description=dept_data.description,
                    cost_center_code=dept_data.cost_center_code,
                    manager_id=manager_id
                ),
                actor_id=token.user_id
            )
        else:
            # Create
            new_dept = await org_service.create_department(
                DepartmentCreate(
                    code=dept_data.code,
                    name=dept_data.name,
                    description=dept_data.description,
                    cost_center_code=dept_data.cost_center_code,
                    manager_id=manager_id
                ),
                actor_id=token.user_id
            )
            dept_id = new_dept.id
            results["departments"] += 1
            
        # 2. Handle Services
        for svc_data in dept_data.services:
            existing_svc = await org_service._service_repo.get_by_code(svc_data.code)
            
            coord_id = None
            if svc_data.coordinator_email:
                user = await user_service._user_repo.get_by_email(svc_data.coordinator_email)
                if user:
                    coord_id = user.id
                    
            if existing_svc:
                await org_service.update_service(
                    existing_svc.id,
                    OrganizationalServiceUpdate(
                        name=svc_data.name,
                        description=svc_data.description,
                        department_id=dept_id,
                        coordinator_id=coord_id
                    ),
                    actor_id=token.user_id
                )
            else:
                # Create
                await org_service.create_service(
                    OrganizationalServiceCreate(
                        code=svc_data.code,
                        name=svc_data.name,
                        description=svc_data.description,
                        department_id=dept_id,
                        coordinator_id=coord_id
                    ),
                    actor_id=token.user_id
                )
                results["services"] += 1
                
    return results

@router.post("/setup/users", response_model=dict)
async def setup_users(
    payload: SetupUsersPayload,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    org_service: OrganizationService = Depends(get_org_service),
    user_service: UserService = Depends(get_user_service)
):
    """Bulk setup/import of Users and their profiles/org mapping."""
    results = {"created": 0, "updated": 0, "errors": []}
    
    # Pre-fetch maps for performance
    depts = await org_service.get_departments()
    dept_map = {d.code: d.id for d in depts}
    
    svcs = await org_service.get_services()
    svc_map = {s.code: s.id for s in svcs}
    
    exec_levels = await org_service.get_executive_levels()
    exec_map = {e.code: e.id for e in exec_levels}
    
    locations = await user_service.get_locations()
    loc_map = {l.code: l.id for l in locations}
    
    contract_types = await user_service.get_contract_types()
    ct_map = {c.code: c.id for c in contract_types}
    
    schedules = await user_service.get_work_schedules()
    sched_map = {s.code: s.id for s in schedules}

    for user_data in payload.users:
        try:
            # Resolve foreign keys
            dept_id = dept_map.get(user_data.department_code) if user_data.department_code else None
            svc_id = svc_map.get(user_data.service_code) if user_data.service_code else None
            exec_id = exec_map.get(user_data.executive_level_code) if user_data.executive_level_code else None
            loc_id = loc_map.get(user_data.location_code) if user_data.location_code else None
            ct_id = ct_map.get(user_data.contract_type_code) if user_data.contract_type_code else None
            sched_id = sched_map.get(user_data.work_schedule_code) if user_data.work_schedule_code else None
            
            manager_id = None
            if user_data.manager_email:
                manager = await user_service._user_repo.get_by_email(user_data.manager_email)
                if manager:
                    manager_id = manager.id

            existing = await user_service._user_repo.get_by_email(user_data.email)
            
            if existing:
                # Update
                update_data = UserUpdate(
                    first_name=user_data.first_name,
                    last_name=user_data.last_name,
                    badge_number=user_data.badge_number,
                    fiscal_code=user_data.fiscal_code,
                    hire_date=user_data.hire_date,
                    department_id=dept_id,
                    service_id=svc_id,
                    executive_level_id=exec_id,
                    location_id=loc_id,
                    contract_type_id=ct_id,
                    work_schedule_id=sched_id,
                    manager_id=manager_id,
                    is_admin=user_data.is_admin,
                    is_manager=user_data.is_manager,
                    is_hr=user_data.is_hr,
                    is_employee=user_data.is_employee,
                    is_active=True
                )
                await user_service.update_user(existing.id, update_data, actor_id=token.user_id)
                results["updated"] += 1
            else:
                user_create = UserCreate(
                    email=user_data.email,
                    username=user_data.username,
                    first_name=user_data.first_name,
                    last_name=user_data.last_name,
                    badge_number=user_data.badge_number,
                    fiscal_code=user_data.fiscal_code,
                    hire_date=user_data.hire_date,
                    keycloak_id=user_data.keycloak_id,
                    is_admin=user_data.is_admin,
                    is_manager=user_data.is_manager,
                    is_hr=user_data.is_hr,
                    is_employee=user_data.is_employee
                )
                # Direct repo create for setup (fast)
                user = await user_service._user_repo.create(**user_create.model_dump())
                # Assign org info & relations
                await user_service._user_repo.update(
                    user.id,
                    department_id=dept_id,
                    service_id=svc_id,
                    executive_level_id=exec_id,
                    location_id=loc_id,
                    contract_type_id=ct_id,
                    work_schedule_id=sched_id,
                    manager_id=manager_id
                )
                results["created"] += 1
        except Exception as e:
            results["errors"].append(f"Error setup user {user_data.email}: {str(e)}")

    await user_service._session.commit()
    return results

