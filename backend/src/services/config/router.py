"""KRONOS Config Service - API Router."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.config import settings
from src.core.security import get_current_token, require_admin, TokenPayload
from src.core.exceptions import NotFoundError, ConflictError
from src.shared.schemas import MessageResponse
from src.services.config.service import ConfigService
from src.services.config.schemas import (
    SystemConfigResponse,
    SystemConfigCreate,
    SystemConfigUpdate,
    ConfigValueResponse,
    LeaveTypeResponse,
    LeaveTypeListResponse,
    LeaveTypeCreate,
    LeaveTypeUpdate,
    HolidayResponse,
    HolidayListResponse,
    HolidayCreate,
    GenerateHolidaysRequest,
    ExpenseTypeResponse,
    ExpenseTypeCreate,
    DailyAllowanceRuleResponse,
    DailyAllowanceRuleCreate,
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
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Clear Redis cache. Admin only."""
    await service.clear_cache()
    return MessageResponse(message="Cache cleared successfully")


@router.get("/config", response_model=list[SystemConfigResponse])
async def list_configs(
    category: Optional[str] = None,
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """List all system configurations. Admin only."""
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
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Create new config entry. Admin only."""
    try:
        return await service.create_config(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/config/{key}", response_model=ConfigValueResponse)
async def update_config(
    key: str,
    data: SystemConfigUpdate,
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Update config value. Admin only."""
    try:
        await service.set(key, data.value)
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
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Create new leave type. Admin only."""
    try:
        return await service.create_leave_type(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/leave-types/{id}", response_model=LeaveTypeResponse)
async def update_leave_type(
    id: UUID,
    data: LeaveTypeUpdate,
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Update leave type. Admin only."""
    try:
        return await service.update_leave_type(id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/leave-types/{id}", response_model=MessageResponse)
async def delete_leave_type(
    id: UUID,
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Deactivate leave type. Admin only."""
    try:
        await service.delete_leave_type(id)
        return MessageResponse(message="Leave type deactivated")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Holidays Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/holidays", response_model=HolidayListResponse)
async def list_holidays(
    year: int,
    location_id: Optional[UUID] = None,
    service: ConfigService = Depends(get_config_service),
):
    """List holidays for a year."""
    holidays = await service.get_holidays(year, location_id)
    return HolidayListResponse(items=holidays, year=year, total=len(holidays))


@router.post("/holidays", response_model=HolidayResponse, status_code=201)
async def create_holiday(
    data: HolidayCreate,
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Create new holiday. Admin only."""
    try:
        return await service.create_holiday(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/holidays/{id}", response_model=MessageResponse)
async def delete_holiday(
    id: UUID,
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Delete holiday. Admin only."""
    try:
        await service.delete_holiday(id)
        return MessageResponse(message="Holiday deleted")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/holidays/generate", response_model=list[HolidayResponse])
async def generate_holidays(
    data: GenerateHolidaysRequest,
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Generate Italian national holidays for a year. Admin only."""
    return await service.generate_holidays(data)


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
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Create new expense type. Admin only."""
    try:
        return await service.create_expense_type(data)
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
    token: TokenPayload = Depends(require_admin),
    service: ConfigService = Depends(get_config_service),
):
    """Create new allowance rule. Admin only."""
    try:
        return await service.create_allowance_rule(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
