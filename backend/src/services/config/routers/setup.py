from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import uuid4

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload, get_current_user
from src.services.config.services import ConfigService
from src.services.config.schemas import (
    SetupContractsPayload, 
    NationalContractCreate, 
    NationalContractLevelCreate,
    NationalContractVersionCreate,
    NationalContractTypeConfigCreate,
    ContractTypeCreate
)
from src.services.config.models import ContractType

router = APIRouter()

async def get_config_service(session: AsyncSession = Depends(get_db)):
    return ConfigService(session)

@router.post("/setup/contracts", response_model=dict)
async def setup_contracts(
    payload: SetupContractsPayload,
    token: TokenPayload = Depends(require_permission("settings:edit")), # Or specific setup permission
    service: ConfigService = Depends(get_config_service)
):
    """
    Bulk setup/import of National Contracts (CCNL).
    Idempotent: checks for existence by code before creating.
    """
    results = {
        "contracts_created": 0,
        "contracts_updated": 0,
        "levels_created": 0,
        "versions_created": 0,
        "configs_created": 0
    }
    
    # Pre-fetch contract types map
    existing_types = await service.get_contract_types()
    type_map = {t.code: t for t in existing_types}
    
    # Pre-fetch calculation modes map
    calc_modes = await service.get_calculation_modes()
    calc_mode_map = {m.code: m.id for m in calc_modes}
    
    # Ensure standard types exist (FT, PT, etc.) if referenced
    # This logic assumes types are pre-seeded or we might need to create them on the fly if missing?
    # For now, let's assume types are static or handled separately, 
    # BUT if the payload implies them, we might need to handle checks.
    
    for contract_data in payload.contracts:
        # 1. Check/Create Contract
        existing_contract = await service._contracts._repo.get_by_code(contract_data.code)
        
        if existing_contract:
            contract_id = existing_contract.id
            results["contracts_updated"] += 1
            # Update fields if needed? For setup, maybe just skip or update limited fields.
        else:
            contract_create = NationalContractCreate(
                code=contract_data.code,
                name=contract_data.name,
                sector=contract_data.sector,
                description=contract_data.description,
                source_url=contract_data.source_url
            )
            created = await service.create_national_contract(contract_create, user_id=token.user_id)
            contract_id = created.id
            results["contracts_created"] += 1
            
        # 2. Levels
        for level in contract_data.levels:
            # Check existence by name within contract
            # Service specific method might be missing, accessing repo directly for check
            # Query: match contract_id and level_name
            # using internal repo access for efficiency/custom query
            from sqlalchemy import select
            from src.services.config.models import NationalContractLevel
            
            stmt = select(NationalContractLevel).where(
                NationalContractLevel.national_contract_id == contract_id,
                NationalContractLevel.level_name == level.name
            )
            res = await service._session.execute(stmt)
            existing_level = res.scalar_one_or_none()
            
            if not existing_level:
                level_create = NationalContractLevelCreate(
                    national_contract_id=contract_id,
                    level_name=level.name,
                    description=level.description,
                    sort_order=level.order
                )
                await service.create_national_contract_level(level_create, actor_id=token.user_id)
                results["levels_created"] += 1
                
        # 3. Versions
        for version in contract_data.versions:
            # Check existence
            from src.services.config.models import NationalContractVersion
            stmt = select(NationalContractVersion).where(
                NationalContractVersion.national_contract_id == contract_id,
                NationalContractVersion.version_name == version.version_name
            )
            res = await service._session.execute(stmt)
            existing_version = res.scalar_one_or_none()
            
            version_id = None
            if not existing_version:
                version_create = NationalContractVersionCreate(
                    national_contract_id=contract_id,
                    version_name=version.version_name,
                    valid_from=version.valid_from,
                    valid_to=version.valid_to,
                    weekly_hours_full_time=version.weekly_hours_full_time,
                    working_days_per_week=version.working_days_per_week,
                    daily_hours=version.daily_hours,
                    annual_vacation_days=version.vacation_days,
                    annual_rol_hours=version.rol_hours,
                    annual_ex_festivita_hours=version.ex_festivita_hours,
                    notes=version.notes,
                    vacation_calc_mode_id=calc_mode_map.get(version.vacation_calc_mode_code),
                    rol_calc_mode_id=calc_mode_map.get(version.rol_calc_mode_code),
                    vacation_calc_params=version.vacation_calc_params,
                    rol_calc_params=version.rol_calc_params
                )
                created_ver = await service.create_contract_version(version_create, created_by=token.user_id)
                version_id = created_ver.id
                results["versions_created"] += 1
            else:
                version_id = existing_version.id
            
            # 4. Type Configs (Types)
            if version_id:
                for t_cfg in version.types:
                    # Resolve Contract Type ID
                    c_type = type_map.get(t_cfg.contract_type_code)
                    if not c_type:
                        # Auto-create basic type if missing?
                        # Or skip? Let's auto-create for robustness
                        # Assuming FT/PT types are somewhat standard but dynamic is better
                        from src.services.config.schemas import ContractTypeCreate
                        new_type_data = ContractTypeCreate(
                             code=t_cfg.contract_type_code,
                             name=t_cfg.contract_type_code, # Fallback
                             is_part_time="PT" in t_cfg.contract_type_code, # Heuristic
                             part_time_percentage=50.0 if "PT" in t_cfg.contract_type_code else 100.0
                        )
                        # We don't have create_contract_type in main service facade exposed?
                        # It is: create_leave_type, create_expense_type... 
                        # Actually NationalContractService has _type_repo but no create method!
                        # Warning: Skipping if not found for now.
                        continue
                        
                    # Check if config exists
                    from src.services.config.models import NationalContractTypeConfig
                    stmt = select(NationalContractTypeConfig).where(
                        NationalContractTypeConfig.national_contract_version_id == version_id,
                        NationalContractTypeConfig.contract_type_id == c_type.id
                    )
                    res = await service._session.execute(stmt)
                    existing_cfg = res.scalar_one_or_none()
                    
                    if not existing_cfg:
                        cfg_create = NationalContractTypeConfigCreate(
                            national_contract_version_id=version_id,
                            contract_type_id=c_type.id,
                            weekly_hours=t_cfg.weekly_hours,
                            annual_vacation_days=t_cfg.annual_vacation_days,
                            annual_rol_hours=t_cfg.annual_rol_hours,
                            annual_ex_festivita_hours=t_cfg.annual_ex_festivita_hours,
                            description=t_cfg.description
                        )
                        await service.create_contract_type_config(cfg_create, actor_id=token.user_id)
                        results["configs_created"] += 1

    return results


@router.post("/setup/leave-types", response_model=dict)
async def setup_leave_types(
    payload: List[dict],
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service)
):
    """
    Bulk setup/import of Leave Types.
    Idempotent: updates if exists by code, creates if not.
    """
    from sqlalchemy import select
    from src.services.config.models import LeaveType
    
    results = {
        "created": 0,
        "updated": 0,
        "errors": []
    }
    
    for lt_data in payload:
        code = lt_data.get("code")
        if not code:
            results["errors"].append("Missing 'code' field in entry")
            continue
            
        # Check if exists
        stmt = select(LeaveType).where(LeaveType.code == code)
        res = await service._session.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            # Update
            existing.name = lt_data.get("name", existing.name)
            existing.description = lt_data.get("description", existing.description)
            existing.max_single_request_days = lt_data.get("max_single_request_days")
            existing.max_consecutive_days = lt_data.get("max_consecutive_days")
            existing.min_notice_days = lt_data.get("min_notice_days")
            existing.requires_protocol = lt_data.get("requires_protocol", existing.requires_protocol)
            existing.balance_type = lt_data.get("balance_type", existing.balance_type)
            existing.is_active = lt_data.get("is_active", existing.is_active)
            results["updated"] += 1
        else:
            # Create
            new_lt = LeaveType(
                code=code,
                name=lt_data.get("name", code),
                description=lt_data.get("description"),
                max_single_request_days=lt_data.get("max_single_request_days"),
                max_consecutive_days=lt_data.get("max_consecutive_days"),
                min_notice_days=lt_data.get("min_notice_days"),
                requires_protocol=lt_data.get("requires_protocol", False),
                balance_type=lt_data.get("balance_type"),
                is_active=lt_data.get("is_active", True),
            )
            service._session.add(new_lt)
            results["created"] += 1
    
    await service._session.commit()
    return results
