"""KRONOS Audit Service - API Router."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_admin, TokenPayload
from src.core.exceptions import NotFoundError
from src.shared.schemas import DataTableRequest
from src.services.audit.service import AuditService
from src.services.audit.schemas import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogListItem,
    AuditLogDataTableResponse,
    AuditLogFilter,
    AuditTrailCreate,
    AuditTrailResponse,
    AuditTrailListItem,
    EntityHistoryResponse,
)


router = APIRouter()


async def get_audit_service(
    session: AsyncSession = Depends(get_db),
) -> AuditService:
    """Dependency for AuditService."""
    return AuditService(session)


# ═══════════════════════════════════════════════════════════
# Audit Log Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/audit/logs", response_model=AuditLogResponse, status_code=201)
async def create_log(
    data: AuditLogCreate,
    service: AuditService = Depends(get_audit_service),
):
    """Create audit log entry. Called by other services."""
    return await service.log_action(data)


@router.get("/audit/logs", response_model=list[AuditLogListItem])
async def get_logs(
    user_id: Optional[UUID] = None,
    user_email: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    service_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    token: TokenPayload = Depends(require_admin),
    svc: AuditService = Depends(get_audit_service),
):
    """Get audit logs with filters. Admin only."""
    filters = AuditLogFilter(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        service_name=service_name,
        status=status,
    )
    
    logs = await svc.get_logs(filters, limit, offset)
    return [AuditLogListItem.model_validate(log) for log in logs]


@router.post("/audit/logs/datatable", response_model=AuditLogDataTableResponse)
async def logs_datatable(
    request: DataTableRequest,
    resource_type: Optional[str] = None,
    service_name: Optional[str] = None,
    token: TokenPayload = Depends(require_admin),
    svc: AuditService = Depends(get_audit_service),
):
    """Get audit logs for DataTable. Admin only."""
    filters = AuditLogFilter(
        resource_type=resource_type,
        service_name=service_name,
    )
    
    logs, total, filtered = await svc.get_logs_datatable(request, filters)
    
    return AuditLogDataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=[AuditLogListItem.model_validate(log) for log in logs],
    )


@router.get("/audit/logs/{id}", response_model=AuditLogResponse)
async def get_log(
    id: UUID,
    token: TokenPayload = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
):
    """Get audit log by ID. Admin only."""
    try:
        return await service.get_log(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/audit/logs/resource/{resource_type}/{resource_id}")
async def get_resource_logs(
    resource_type: str,
    resource_id: str,
    limit: int = Query(default=50, le=200),
    token: TokenPayload = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
):
    """Get all logs for a specific resource. Admin only."""
    logs = await service.get_resource_logs(resource_type, resource_id, limit)
    return [AuditLogListItem.model_validate(log) for log in logs]


# ═══════════════════════════════════════════════════════════
# Audit Trail Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/audit/trail", response_model=AuditTrailResponse, status_code=201)
async def record_change(
    data: AuditTrailCreate,
    service: AuditService = Depends(get_audit_service),
):
    """Record entity change. Called by other services."""
    return await service.record_change(data)


@router.get("/audit/trail/{entity_type}/{entity_id}", response_model=EntityHistoryResponse)
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    token: TokenPayload = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
):
    """Get complete history for an entity. Admin only."""
    try:
        return await service.get_entity_history(entity_type, entity_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/audit/trail/{entity_type}/{entity_id}/version/{version}", response_model=AuditTrailResponse)
async def get_entity_version(
    entity_type: str,
    entity_id: str,
    version: int,
    token: TokenPayload = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
):
    """Get specific version of an entity. Admin only."""
    try:
        return await service.get_entity_version(entity_type, entity_id, version)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/audit/trail/{entity_type}/{entity_id}/compare")
async def compare_versions(
    entity_type: str,
    entity_id: str,
    v1: int = Query(..., description="First version"),
    v2: int = Query(..., description="Second version"),
    token: TokenPayload = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
):
    """Compare two versions of an entity. Admin only."""
    try:
        return await service.compare_versions(entity_type, entity_id, v1, v2)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/audit/trail/user/{user_id}", response_model=list[AuditTrailListItem])
async def get_user_changes(
    user_id: UUID,
    limit: int = Query(default=50, le=200),
    token: TokenPayload = Depends(require_admin),
    service: AuditService = Depends(get_audit_service),
):
    """Get all changes made by a user. Admin only."""
    changes = await service.get_user_changes(user_id, limit)
    return [AuditTrailListItem.model_validate(c) for c in changes]
