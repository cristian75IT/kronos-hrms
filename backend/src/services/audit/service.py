"""KRONOS Audit Service - Business Logic."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.services.audit.repository import AuditLogRepository, AuditTrailRepository
from src.services.audit.schemas import (
    AuditLogCreate,
    AuditLogFilter,
    AuditTrailCreate,
    EntityHistoryResponse,
    AuditTrailResponse,
)
from src.shared.schemas import DataTableRequest


class AuditService:
    """Service for audit logging and trail management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._log_repo = AuditLogRepository(session)
        self._trail_repo = AuditTrailRepository(session)

    # ═══════════════════════════════════════════════════════════
    # Audit Log Operations
    # ═══════════════════════════════════════════════════════════

    async def log_action(self, data: AuditLogCreate):
        """Log an action to audit log."""
        return await self._log_repo.create(**data.model_dump())

    async def get_log(self, id: UUID):
        """Get audit log by ID."""
        log = await self._log_repo.get(id)
        if not log:
            raise NotFoundError("Audit log not found")
        return log

    async def get_logs(
        self,
        filters: AuditLogFilter,
        limit: int = 100,
        offset: int = 0,
    ):
        """Get logs by filters."""
        return await self._log_repo.get_by_filters(filters, limit, offset)

    async def get_logs_datatable(
        self,
        request: DataTableRequest,
        filters: Optional[AuditLogFilter] = None,
    ):
        """Get logs for DataTable."""
        return await self._log_repo.get_datatable(request, filters)

    async def get_resource_logs(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ):
        """Get all logs for a specific resource."""
        return await self._log_repo.get_by_resource(resource_type, resource_id, limit)

    # ═══════════════════════════════════════════════════════════
    # Audit Trail Operations
    # ═══════════════════════════════════════════════════════════

    async def record_change(self, data: AuditTrailCreate):
        """Record an entity change to audit trail."""
        return await self._trail_repo.create(**data.model_dump())

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
    ) -> EntityHistoryResponse:
        """Get complete history for an entity."""
        history = await self._trail_repo.get_entity_history(entity_type, entity_id)
        
        if not history:
            raise NotFoundError(f"No history found for {entity_type}:{entity_id}")
        
        return EntityHistoryResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            current_version=history[0].version if history else 0,
            history=[AuditTrailResponse.model_validate(h) for h in history],
        )

    async def get_entity_version(
        self,
        entity_type: str,
        entity_id: str,
        version: int,
    ):
        """Get a specific version of an entity."""
        trail = await self._trail_repo.get_version(entity_type, entity_id, version)
        if not trail:
            raise NotFoundError(f"Version {version} not found for {entity_type}:{entity_id}")
        return trail

    async def compare_versions(
        self,
        entity_type: str,
        entity_id: str,
        version1: int,
        version2: int,
    ) -> dict:
        """Compare two versions of an entity."""
        v1 = await self._trail_repo.get_version(entity_type, entity_id, version1)
        v2 = await self._trail_repo.get_version(entity_type, entity_id, version2)
        
        if not v1 or not v2:
            raise NotFoundError("One or both versions not found")
        
        # Get data from appropriate field
        data1 = v1.after_data if v1.operation != "DELETE" else v1.before_data
        data2 = v2.after_data if v2.operation != "DELETE" else v2.before_data
        
        # Find differences
        differences = {}
        all_keys = set((data1 or {}).keys()) | set((data2 or {}).keys())
        
        for key in all_keys:
            val1 = (data1 or {}).get(key)
            val2 = (data2 or {}).get(key)
            
            if val1 != val2:
                differences[key] = {
                    f"version_{version1}": val1,
                    f"version_{version2}": val2,
                }
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "version1": version1,
            "version2": version2,
            "differences": differences,
        }

    async def get_user_changes(
        self,
        user_id: UUID,
        limit: int = 50,
    ):
        """Get all changes made by a user."""
        return await self._trail_repo.get_changes_by_user(user_id, limit)

    # ═══════════════════════════════════════════════════════════
    # Helper for other services
    # ═══════════════════════════════════════════════════════════

    async def track_entity(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        before_data: Optional[dict] = None,
        after_data: Optional[dict] = None,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None,
        change_reason: Optional[str] = None,
        service_name: str = "unknown",
        request_id: Optional[str] = None,
    ):
        """Convenience method for tracking entity changes.
        
        Called by other services via HTTP or message queue.
        """
        # Calculate changed fields
        changed_fields = None
        if before_data and after_data and operation == "UPDATE":
            changed_fields = [
                key for key in set(before_data.keys()) | set(after_data.keys())
                if before_data.get(key) != after_data.get(key)
            ]
        
        return await self._trail_repo.create(
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            before_data=before_data,
            after_data=after_data,
            changed_fields=changed_fields,
            changed_by=changed_by,
            changed_by_email=changed_by_email,
            change_reason=change_reason,
            service_name=service_name,
            request_id=request_id,
        )

    # ═══════════════════════════════════════════════════════════
    # Enterprise Statistics
    # ═══════════════════════════════════════════════════════════

    async def get_stats_summary(self, days: int = 7) -> dict:
        """Get audit statistics summary."""
        return await self._log_repo.get_stats_summary(days)

    async def get_stats_by_service(self, days: int = 7) -> list[dict]:
        """Get audit stats grouped by service."""
        return await self._log_repo.get_stats_by_service(days)

    async def get_stats_by_action(
        self, 
        days: int = 7, 
        service_name: Optional[str] = None
    ) -> list[dict]:
        """Get audit stats grouped by action."""
        return await self._log_repo.get_stats_by_action(days, service_name)

    # ═══════════════════════════════════════════════════════════
    # Data Retention
    # ═══════════════════════════════════════════════════════════

    async def archive_logs(self, retention_days: int = 90) -> int:
        """Archive old audit logs."""
        return await self._log_repo.archive_old_logs(retention_days)

    async def purge_archives(self, archive_retention_days: int = 365) -> int:
        """Purge old archived logs for GDPR compliance."""
        return await self._log_repo.purge_archives(archive_retention_days)

