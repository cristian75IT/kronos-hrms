"""KRONOS Audit Service - API Router."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_permission, TokenPayload
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
    token: TokenPayload = Depends(require_permission("audit:view")),
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
    token: TokenPayload = Depends(require_permission("audit:view")),
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
    token: TokenPayload = Depends(require_permission("audit:view")),
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
    token: TokenPayload = Depends(require_permission("audit:view")),
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
    token: TokenPayload = Depends(require_permission("audit:view")),
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
    token: TokenPayload = Depends(require_permission("audit:view")),
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
    token: TokenPayload = Depends(require_permission("audit:view")),
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
    token: TokenPayload = Depends(require_permission("audit:view")),
    service: AuditService = Depends(get_audit_service),
):
    """Get all changes made by a user. Admin only."""
    changes = await service.get_user_changes(user_id, limit)
    return [AuditTrailListItem.model_validate(c) for c in changes]


# ═══════════════════════════════════════════════════════════════════
# Enterprise Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.get("/audit/stats/summary")
async def get_audit_stats_summary(
    days: int = Query(default=7, le=90, description="Number of days to include"),
    token: TokenPayload = Depends(require_permission("audit:view")),
    svc: AuditService = Depends(get_audit_service),
):
    """Get audit statistics summary. Admin only."""
    return await svc.get_stats_summary(days)


@router.get("/audit/stats/by-service")
async def get_stats_by_service(
    days: int = Query(default=7, le=90),
    token: TokenPayload = Depends(require_permission("audit:view")),
    svc: AuditService = Depends(get_audit_service),
):
    """Get audit stats grouped by service. Admin only."""
    return await svc.get_stats_by_service(days)


@router.get("/audit/stats/by-action")
async def get_stats_by_action(
    days: int = Query(default=7, le=90),
    service_name: Optional[str] = None,
    token: TokenPayload = Depends(require_permission("audit:view")),
    svc: AuditService = Depends(get_audit_service),
):
    """Get audit stats grouped by action. Admin only."""
    return await svc.get_stats_by_action(days, service_name)


@router.get("/audit/export")
async def export_audit_logs(
    format: str = Query(default="json", regex="^(json|csv)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    service_name: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(default=1000, le=10000),
    token: TokenPayload = Depends(require_permission("audit:export")),
    svc: AuditService = Depends(get_audit_service),
):
    """Export audit logs for compliance. Admin only."""
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    import csv
    import io
    import json
    
    # Parse dates
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    filters = AuditLogFilter(
        service_name=service_name,
        resource_type=resource_type,
        start_date=start,
        end_date=end,
    )
    
    logs = await svc.get_logs(filters, limit=limit, offset=0)
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "ID", "Timestamp", "User Email", "Service", "Action",
            "Resource Type", "Resource ID", "Status", "Description"
        ])
        
        # Data
        for log in logs:
            writer.writerow([
                str(log.id),
                log.created_at.isoformat(),
                log.user_email or "",
                log.service_name,
                log.action,
                log.resource_type,
                log.resource_id or "",
                log.status,
                log.description or "",
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_export.csv"}
        )
    else:
        # JSON export
        data = [
            {
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "user_email": log.user_email,
                "service_name": log.service_name,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "status": log.status,
                "description": log.description,
            }
            for log in logs
        ]
        
        output = io.BytesIO()
        output.write(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit_export.json"}
        )


@router.post("/audit/archive")
async def archive_old_logs(
    retention_days: int = Query(default=90, ge=30, le=365),
    token: TokenPayload = Depends(require_permission("audit:manage")),
    svc: AuditService = Depends(get_audit_service),
):
    """Archive old audit logs. Admin only."""
    archived_count = await svc.archive_logs(retention_days)
    return {"archived_count": archived_count, "retention_days": retention_days}


@router.post("/audit/purge-archives")
async def purge_old_archives(
    archive_retention_days: int = Query(default=365, ge=180, le=2555),
    token: TokenPayload = Depends(require_permission("audit:manage")),
    svc: AuditService = Depends(get_audit_service),
):
    """Purge old archived logs for GDPR compliance. Admin only."""
    purged_count = await svc.purge_archives(archive_retention_days)
    return {"purged_count": purged_count, "archive_retention_days": archive_retention_days}
