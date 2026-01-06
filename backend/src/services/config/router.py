"""KRONOS Config Service - API Router."""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.config import settings
from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError, ConflictError
from src.shared.schemas import MessageResponse
from src.services.config.services import ConfigService
from src.services.config.schemas import (
    SystemConfigResponse,
    SystemConfigCreate,
    SystemConfigUpdate,
    ConfigValueResponse,
    LeaveTypeResponse,
    LeaveTypeListResponse,
    LeaveTypeCreate,
    LeaveTypeUpdate,
    # Note: Holiday and Closure schemas moved to Calendar Service
    ExpenseTypeResponse,
    ExpenseTypeCreate,
    DailyAllowanceRuleResponse,
    DailyAllowanceRuleCreate,
    NationalContractLevelCreate,
    NationalContractLevelUpdate,
    NationalContractLevelResponse,
    NationalContractResponse,
    NationalContractCreate,
    NationalContractUpdate,
    NationalContractListResponse,
    NationalContractVersionResponse,
    NationalContractVersionCreate,
    NationalContractVersionUpdate,
    NationalContractVersionListResponse,
    NationalContractTypeConfigResponse,
    NationalContractTypeConfigUpdate,
    ContractTypeResponse,
    NationalContractTypeConfigCreate,
    CalculationModeResponse,
    CalculationModeListResponse,
    CalculationModeCreate,
    CalculationModeUpdate,
)


router = APIRouter()


# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    """Get Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url)
            await _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


async def get_config_service(
    session: AsyncSession = Depends(get_db),
    redis_client: Optional[redis.Redis] = Depends(get_redis),
) -> ConfigService:
    """Dependency for ConfigService."""
    return ConfigService(session, redis_client)


# ═══════════════════════════════════════════════════════════
# System Config Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/config/cache/clear", response_model=MessageResponse)
async def clear_cache(
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Clear Redis cache. Admin only."""
    await service.clear_cache()
    return MessageResponse(message="Cache cleared successfully")


@router.get("/config", response_model=list[SystemConfigResponse])
async def list_configs(
    category: Optional[str] = None,
    token: TokenPayload = Depends(get_current_user),  # Any authenticated user can view
    service: ConfigService = Depends(get_config_service),
):
    """List all system configurations. Any authenticated user can view."""
    if category:
        configs = await service._config_repo.get_by_category(category)
    else:
        configs = await service.get_all()
    return configs


@router.get("/config/{key}", response_model=ConfigValueResponse)
async def get_config(
    key: str,
    # Relaxed for service-to-service communication
    service: ConfigService = Depends(get_config_service),
):
    """Get single config value. Admin only."""
    value = await service.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Config not found: {key}")
    return ConfigValueResponse(key=key, value=value)


@router.post("/config", response_model=SystemConfigResponse, status_code=201)
async def create_config(
    data: SystemConfigCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new config entry. Admin only."""
    try:
        return await service.create_config(data, user_id=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/config/{key}", response_model=ConfigValueResponse)
async def update_config(
    key: str,
    data: SystemConfigUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Update config value. Admin only."""
    try:
        await service.set(key, data.value, user_id=token.user_id)
        return ConfigValueResponse(key=key, value=data.value)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Leave Types Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/leave-types", response_model=LeaveTypeListResponse)
async def list_leave_types(
    active_only: bool = True,
    service: ConfigService = Depends(get_config_service),
):
    """List all leave types."""
    types = await service.get_leave_types(active_only)
    return LeaveTypeListResponse(items=types, total=len(types))


@router.get("/leave-types/{id}", response_model=LeaveTypeResponse)
async def get_leave_type(
    id: UUID,
    service: ConfigService = Depends(get_config_service),
):
    """Get leave type by ID."""
    try:
        return await service.get_leave_type(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/leave-types", response_model=LeaveTypeResponse, status_code=201)
async def create_leave_type(
    data: LeaveTypeCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new leave type. Admin only."""
    try:
        return await service.create_leave_type(data, user_id=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/leave-types/{id}", response_model=LeaveTypeResponse)
async def update_leave_type(
    id: UUID,
    data: LeaveTypeUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Update leave type. Admin only."""
    try:
        return await service.update_leave_type(id, data, user_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/leave-types/{id}", response_model=MessageResponse)
async def delete_leave_type(
    id: UUID,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Deactivate leave type. Admin only."""
    try:
        await service.delete_leave_type(id, user_id=token.user_id)
        return MessageResponse(message="Leave type deactivated")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# NOTE: Holidays and Closures have been migrated to Calendar Service
# Use Calendar Service endpoints at /api/v1/calendar/holidays and /api/v1/calendar/closures
# ═══════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════
# Expense Types Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/expense-types", response_model=list[ExpenseTypeResponse])
async def list_expense_types(
    active_only: bool = True,
    service: ConfigService = Depends(get_config_service),
):
    """List all expense types."""
    return await service.get_expense_types(active_only)


@router.post("/expense-types", response_model=ExpenseTypeResponse, status_code=201)
async def create_expense_type(
    data: ExpenseTypeCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new expense type. Admin only."""
    try:
        return await service.create_expense_type(data, actor_id=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Daily Allowance Rules Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/allowance-rules", response_model=list[DailyAllowanceRuleResponse])
async def list_allowance_rules(
    service: ConfigService = Depends(get_config_service),
):
    """List all daily allowance rules."""
    return await service.get_allowance_rules()


@router.post("/allowance-rules", response_model=DailyAllowanceRuleResponse, status_code=201)
async def create_allowance_rule(
    data: DailyAllowanceRuleCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new allowance rule. Admin only."""
    try:
        return await service.create_allowance_rule(data, actor_id=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Calculation Modes Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/calculation-modes", response_model=CalculationModeListResponse)
async def list_calculation_modes(
    service: ConfigService = Depends(get_config_service),
):
    """List all calculation modes."""
    modes = await service.get_calculation_modes()
    return CalculationModeListResponse(items=modes, total=len(modes))


@router.get("/calculation-modes/{id}", response_model=CalculationModeResponse)
async def get_calculation_mode(
    id: UUID,
    service: ConfigService = Depends(get_config_service),
):
    """Get calculation mode by ID."""
    try:
        return await service.get_calculation_mode(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/calculation-modes", response_model=CalculationModeResponse, status_code=201)
async def create_calculation_mode(
    data: CalculationModeCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new calculation mode. Admin only."""
    try:
        return await service.create_calculation_mode(data, actor_id=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/calculation-modes/{id}", response_model=CalculationModeResponse)
async def update_calculation_mode(
    id: UUID,
    data: CalculationModeUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Update calculation mode. Admin only."""
    try:
        return await service.update_calculation_mode(id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/calculation-modes/{id}", response_model=MessageResponse)
async def delete_calculation_mode(
    id: UUID,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Deactivate calculation mode. Admin only."""
    try:
        await service.delete_calculation_mode(id, actor_id=token.user_id)
        return MessageResponse(message="Calculation mode deactivated")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# National Contracts (CCNL) Endpoints
# ═══════════════════════════════════════════════════════════

from src.services.config.schemas import (
    NationalContractResponse,
    NationalContractListResponse,
    NationalContractCreate,
    NationalContractUpdate,
    NationalContractVersionResponse,
    NationalContractVersionListResponse,
    NationalContractVersionCreate,
    NationalContractVersionUpdate,
    NationalContractTypeConfigResponse,
    NationalContractTypeConfigUpdate,
)


@router.get("/national-contracts", response_model=NationalContractListResponse)
async def list_national_contracts(
    active_only: bool = True,
    token: TokenPayload = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service),
):
    """List all National Contracts (CCNL)."""
    contracts = await service.get_national_contracts(active_only)
    return NationalContractListResponse(items=contracts, total=len(contracts))


@router.get("/national-contracts/{id}", response_model=NationalContractResponse)
async def get_national_contract(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service),
):
    """Get National Contract by ID."""
    try:
        return await service.get_national_contract(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/national-contracts", response_model=NationalContractResponse, status_code=201)
async def create_national_contract(
    data: NationalContractCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new National Contract (CCNL). Admin only."""
    try:
        return await service.create_national_contract(data, user_id=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/national-contracts/{id}", response_model=NationalContractResponse)
async def update_national_contract(
    id: UUID,
    data: NationalContractUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Update National Contract. Admin only."""
    try:
        return await service.update_national_contract(id, data, user_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/national-contracts/{id}", response_model=MessageResponse)
async def delete_national_contract(
    id: UUID,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Deactivate National Contract. Admin only."""
    try:
        await service.delete_national_contract(id, user_id=token.user_id)
        return MessageResponse(message="National Contract deactivated")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# National Contract Versions (CCNL Versions) Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/national-contracts/{contract_id}/versions", response_model=NationalContractVersionListResponse)
async def list_contract_versions(
    contract_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service),
):
    """List all versions of a National Contract."""
    versions = await service.get_contract_versions(contract_id)
    return NationalContractVersionListResponse(items=versions, total=len(versions))


@router.get("/national-contracts/{contract_id}/versions/current", response_model=NationalContractVersionResponse)
async def get_current_contract_version(
    contract_id: UUID,
    reference_date: Optional[date] = None,
    token: TokenPayload = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service),
):
    """Get the version valid at a specific date (defaults to today)."""
    from datetime import date as date_type
    ref_date = reference_date or date_type.today()
    try:
        return await service.get_contract_version_at_date(contract_id, ref_date)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/national-contracts/versions/{version_id}", response_model=NationalContractVersionResponse)
async def get_contract_version(
    version_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service),
):
    """Get a specific version by ID."""
    try:
        return await service.get_contract_version(version_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/national-contracts/versions", response_model=NationalContractVersionResponse, status_code=201)
async def create_contract_version(
    data: NationalContractVersionCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new version for a National Contract. Admin only.
    
    This creates a historical snapshot of parameters valid from the specified date.
    Previous versions will have their valid_to date automatically updated.
    """
    try:
        return await service.create_contract_version(data, created_by=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/national-contracts/versions/{version_id}", response_model=NationalContractVersionResponse)
async def update_contract_version(
    version_id: UUID,
    data: NationalContractVersionUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Update a version. Admin only.
    
    Warning: Modifying historical versions may affect past calculations.
    """
    try:
        return await service.update_contract_version(version_id, data, user_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/national-contracts/versions/{version_id}", response_model=MessageResponse)
async def delete_contract_version(
    version_id: UUID,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Delete a version. Admin only.
    
    Warning: This is a hard delete. Use with caution.
    """
    try:
        await service.delete_contract_version(version_id, user_id=token.user_id)
        return MessageResponse(message="Version deleted")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/contract-types", response_model=list[ContractTypeResponse])
async def list_contract_types(
    token: TokenPayload = Depends(get_current_user),
    service: ConfigService = Depends(get_config_service),
):
    """List all available contract types."""
    return await service.get_contract_types()


@router.post("/national-contracts/type-configs", response_model=NationalContractTypeConfigResponse)
async def create_contract_type_config(
    data: NationalContractTypeConfigCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create a contract type configuration override."""
    return await service.create_contract_type_config(data, actor_id=token.user_id)


@router.delete("/national-contracts/type-configs/{id}", response_model=MessageResponse)
async def delete_contract_type_config(
    id: UUID,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Delete a contract type configuration override."""
    try:
        await service.delete_contract_type_config(id, actor_id=token.user_id)
        return MessageResponse(message="Configuration deleted")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/national-contracts/type-configs/{config_id}", response_model=NationalContractTypeConfigResponse)
async def update_contract_type_config(
    config_id: UUID,
    data: NationalContractTypeConfigUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Update contract type specific parameters."""
    try:
        return await service.update_contract_type_config(config_id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/national-contracts/levels", response_model=NationalContractLevelResponse, status_code=201)
async def create_contract_level(
    data: NationalContractLevelCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Create new contract level."""
    try:
        return await service.create_national_contract_level(data, actor_id=token.user_id)
    except Exception as e:
        # Generic error handling as service methods might raise DB errors
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/national-contracts/levels/{level_id}", response_model=NationalContractLevelResponse)
async def update_contract_level(
    level_id: UUID,
    data: NationalContractLevelUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Update contract level."""
    try:
        return await service.update_national_contract_level(level_id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/national-contracts/levels/{level_id}", response_model=MessageResponse)
async def delete_contract_level(
    level_id: UUID,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ConfigService = Depends(get_config_service),
):
    """Delete contract level."""
    try:
        await service.delete_national_contract_level(level_id, actor_id=token.user_id)
        return MessageResponse(message="Level deleted")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
