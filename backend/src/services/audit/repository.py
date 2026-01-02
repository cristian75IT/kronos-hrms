"""KRONOS Audit Service - Repository Layer."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.audit.models import AuditLog, AuditTrail
from src.services.auth.models import User
from src.services.audit.schemas import AuditLogFilter
from src.shared.schemas import DataTableRequest


class AuditLogRepository:
    """Repository for audit logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[AuditLog]:
        """Get audit log by ID."""
        result = await self._session.execute(
            select(AuditLog, User.first_name, User.last_name)
            .outerjoin(User, AuditLog.user_id == User.id)
            .where(AuditLog.id == id)
        )
        row = result.first()
        if not row:
            return None
            
        log, first_name, last_name = row
        if first_name and last_name:
            setattr(log, 'user_name', f"{first_name} {last_name}")
        else:
             setattr(log, 'user_name', None)
             
        return log

    async def get_by_filters(
        self,
        filters: AuditLogFilter,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get logs by filters."""
        query = select(AuditLog)
        
        if filters.user_id:
            query = query.where(AuditLog.user_id == filters.user_id)
        if filters.user_email:
            query = query.where(AuditLog.user_email.ilike(f"%{filters.user_email}%"))
        if filters.action:
            query = query.where(AuditLog.action == filters.action)
        if filters.resource_type:
            query = query.where(AuditLog.resource_type == filters.resource_type)
        if filters.resource_id:
            query = query.where(AuditLog.resource_id == filters.resource_id)
        if filters.status:
            query = query.where(AuditLog.status == filters.status)
        if filters.channel:
            query = query.where(AuditLog.request_data.op("->>")("channel") == filters.channel)
        if filters.service_name:
            query = query.where(AuditLog.service_name == filters.service_name)
        if filters.start_date:
            query = query.where(AuditLog.created_at >= filters.start_date)
        if filters.end_date:
            query = query.where(AuditLog.created_at <= filters.end_date)
        
        query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
        
        # Execute with User join
        stmt = (
            select(AuditLog, User.first_name, User.last_name)
            .outerjoin(User, AuditLog.user_id == User.id)
            .where(AuditLog.id.in_(select(query.subquery().c.id)))
            .order_by(desc(AuditLog.created_at))
        )
        
        result = await self._session.execute(stmt)
        rows = result.all()
        
        items = []
        for log, first_name, last_name in rows:
            if first_name and last_name:
                setattr(log, 'user_name', f"{first_name} {last_name}")
            else:
                setattr(log, 'user_name', None)
            items.append(log)
            
        return items

    async def get_datatable(
        self,
        request: DataTableRequest,
        filters: Optional[AuditLogFilter] = None,
    ) -> tuple[list[AuditLog], int, int]:
        """Get logs for DataTable."""
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))
        
        # Apply filters
        if filters:
            if filters.user_id:
                query = query.where(AuditLog.user_id == filters.user_id)
                count_query = count_query.where(AuditLog.user_id == filters.user_id)
            if filters.resource_type:
                query = query.where(AuditLog.resource_type == filters.resource_type)
                count_query = count_query.where(AuditLog.resource_type == filters.resource_type)
            if filters.service_name:
                query = query.where(AuditLog.service_name == filters.service_name)
                count_query = count_query.where(AuditLog.service_name == filters.service_name)
            if filters.channel:
                query = query.where(AuditLog.request_data.op("->>")("channel") == filters.channel)
                count_query = count_query.where(AuditLog.request_data.op("->>")("channel") == filters.channel)
        
        # Total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Search
        filtered_count_query = count_query
        if request.search_value:
            search = f"%{request.search_value}%"
            search_filter = (
                AuditLog.user_email.ilike(search) |
                AuditLog.action.ilike(search) |
                AuditLog.resource_type.ilike(search) |
                AuditLog.description.ilike(search)
            )
            query = query.where(search_filter)
            filtered_count_query = filtered_count_query.where(search_filter)
        
        # Filtered count
        filtered_result = await self._session.execute(filtered_count_query)
        filtered = filtered_result.scalar() or total
        
        # Ordering
        query = query.order_by(desc(AuditLog.created_at))
        
        # Pagination
        query = query.offset(request.start).limit(request.length)
        
        # Execute with User join for display
        final_query = (
            select(AuditLog, User.first_name, User.last_name)
            .outerjoin(User, AuditLog.user_id == User.id)
            .where(AuditLog.id.in_(select(query.subquery().c.id)))
            .order_by(desc(AuditLog.created_at))
        )
        
        # Note: The subquery approach is efficient for pagination + join
        # Alternatively, we can just join the main query but we need to ensure unique ID selection if 1:N (here 1:1 so safe)
        
        result = await self._session.execute(final_query)
        rows = result.all()
        
        items = []
        for log, first_name, last_name in rows:
            # Create a dict from the ORM object to inject user_name
            # Since Pydantic from_attributes=True works on objects, we can set a dynamic attribute
            if first_name and last_name:
                setattr(log, 'user_name', f"{first_name} {last_name}")
            else:
                setattr(log, 'user_name', None)
            items.append(log)
            
        return items, total, filtered

    async def create(self, **kwargs: Any) -> AuditLog:
        """Create audit log entry."""
        log = AuditLog(**kwargs)
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get logs for a specific resource."""
        result = await self._session.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id,
                )
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


class AuditTrailRepository:
    """Repository for audit trail."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[AuditTrail]:
        """Get audit trail entry by ID."""
        result = await self._session.execute(
            select(AuditTrail).where(AuditTrail.id == id)
        )
        return result.scalar_one_or_none()

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[AuditTrail]:
        """Get complete history for an entity."""
        result = await self._session.execute(
            select(AuditTrail)
            .where(
                and_(
                    AuditTrail.entity_type == entity_type,
                    AuditTrail.entity_id == entity_id,
                )
            )
            .order_by(AuditTrail.version.desc())
        )
        return list(result.scalars().all())

    async def get_latest_version(
        self,
        entity_type: str,
        entity_id: str,
    ) -> int:
        """Get the latest version number for an entity."""
        result = await self._session.execute(
            select(func.max(AuditTrail.version))
            .where(
                and_(
                    AuditTrail.entity_type == entity_type,
                    AuditTrail.entity_id == entity_id,
                )
            )
        )
        version = result.scalar()
        return version or 0

    async def get_version(
        self,
        entity_type: str,
        entity_id: str,
        version: int,
    ) -> Optional[AuditTrail]:
        """Get a specific version of an entity."""
        result = await self._session.execute(
            select(AuditTrail)
            .where(
                and_(
                    AuditTrail.entity_type == entity_type,
                    AuditTrail.entity_id == entity_id,
                    AuditTrail.version == version,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> AuditTrail:
        """Create audit trail entry."""
        # Get next version
        version = await self.get_latest_version(
            kwargs.get("entity_type", ""),
            kwargs.get("entity_id", ""),
        )
        kwargs["version"] = version + 1
        
        trail = AuditTrail(**kwargs)
        self._session.add(trail)
        await self._session.flush()
        return trail

    async def get_changes_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> list[AuditTrail]:
        """Get changes made by a specific user."""
        result = await self._session.execute(
            select(AuditTrail)
            .where(AuditTrail.changed_by == user_id)
            .order_by(desc(AuditTrail.changed_at))
            .limit(limit)
        )
        return list(result.scalars().all())
