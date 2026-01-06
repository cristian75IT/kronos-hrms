"""
KRONOS - Leave Types Service

Handles leave type management.
"""
import json
from typing import Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ConflictError
from src.shared.audit_client import get_audit_logger
from src.services.config.repository import LeaveTypeRepository
from src.services.config.schemas import LeaveTypeCreate, LeaveTypeUpdate


class LeaveTypeService:
    """
    Service for leave type management with Redis cache.
    
    Handles:
    - Get/list leave types
    - Create/update/delete leave types
    - Cache management
    """
    
    CACHE_PREFIX = "config:"
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(
        self,
        session: AsyncSession,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        self._session = session
        self._leave_type_repo = LeaveTypeRepository(session)
        self._redis = redis_client
        self._audit = get_audit_logger("config-service")
    
    async def get_leave_types(self, active_only: bool = True) -> list:
        """Get all leave types."""
        # Try cache
        if self._redis and active_only:
            cache_key = f"{self.CACHE_PREFIX}leave_types"
            cached = await self._redis.get(cache_key)
            if cached:
                return json.loads(cached)
        
        types = await self._leave_type_repo.get_all(active_only)
        
        # Cache if active only
        if self._redis and active_only:
            await self._redis.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps([self._leave_type_to_dict(t) for t in types]),
            )
        
        return types
    
    async def get_leave_type(self, id: UUID):
        """Get leave type by ID."""
        leave_type = await self._leave_type_repo.get(id)
        if not leave_type:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))
        return leave_type
    
    async def get_leave_type_by_code(self, code: str):
        """Get leave type by code."""
        leave_type = await self._leave_type_repo.get_by_code(code)
        if not leave_type:
            raise NotFoundError(f"Leave type not found: {code}")
        return leave_type
    
    async def create_leave_type(self, data: LeaveTypeCreate, user_id: Optional[UUID] = None):
        """Create new leave type."""
        existing = await self._leave_type_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Leave type code already exists: {data.code}")
        
        leave_type = await self._leave_type_repo.create(**data.model_dump())
        await self._invalidate_cache("leave_types")
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="LEAVE_TYPE",
            resource_id=str(leave_type.id),
            description=f"Created leave type: {leave_type.name} ({leave_type.code})",
            request_data=data.model_dump(mode="json")
        )
        return leave_type
    
    async def update_leave_type(self, id: UUID, data: LeaveTypeUpdate, user_id: Optional[UUID] = None):
        """Update leave type."""
        leave_type = await self._leave_type_repo.update(id, **data.model_dump(exclude_unset=True))
        if not leave_type:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))
        
        await self._invalidate_cache("leave_types")
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="LEAVE_TYPE",
            resource_id=str(id),
            description=f"Updated leave type: {leave_type.name}",
            request_data=data.model_dump(mode="json")
        )
        return leave_type
    
    async def delete_leave_type(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Deactivate leave type."""
        leave_type = await self.get_leave_type(id)
        result = await self._leave_type_repo.deactivate(id)
        if not result:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))
        
        await self._invalidate_cache("leave_types")
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="LEAVE_TYPE",
            resource_id=str(id),
            description=f"Deactivated leave type: {leave_type.name}"
        )
        return True
    
    def _leave_type_to_dict(self, leave_type) -> dict:
        """Convert leave type to dict for caching."""
        return {
            "id": str(leave_type.id),
            "code": leave_type.code,
            "name": leave_type.name,
            "description": leave_type.description,
            "color": leave_type.color,
            "icon": leave_type.icon,
            "sort_order": leave_type.sort_order,
            "scales_balance": leave_type.scales_balance,
            "balance_type": leave_type.balance_type,
            "requires_approval": leave_type.requires_approval,
            "requires_attachment": leave_type.requires_attachment,
            "requires_protocol": leave_type.requires_protocol,
            "min_notice_days": leave_type.min_notice_days,
            "max_consecutive_days": leave_type.max_consecutive_days,
            "max_per_month": leave_type.max_per_month,
            "allow_past_dates": leave_type.allow_past_dates,
            "allow_half_day": leave_type.allow_half_day,
            "allow_negative_balance": leave_type.allow_negative_balance,
            "is_active": leave_type.is_active,
            "created_at": leave_type.created_at.isoformat() if leave_type.created_at else None,
            "updated_at": leave_type.updated_at.isoformat() if leave_type.updated_at else None,
        }
    
    async def _invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache for a specific key."""
        if not self._redis or not key:
            return
        await self._redis.delete(f"{self.CACHE_PREFIX}{key}")
