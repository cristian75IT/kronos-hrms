"""
KRONOS - Leave Service Client

Client for inter-service communication with the Leave Service.
"""
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class LeaveClient(BaseClient):
    """Client for Leave Service interactions (for inter-service communication)."""
    
    def __init__(self):
        super().__init__(
            base_url=settings.leave_service_url,
            service_name="leave",
        )
    
    async def recalculate_for_closure(
        self,
        closure_start: date,
        closure_end: date,
    ) -> Optional[dict]:
        """
        Trigger recalculation of leave requests that overlap with a closure.
        
        Called by calendar service when a company closure is created or modified.
        """
        return await self.post_safe(
            "/api/v1/internal/recalculate-for-closure",
            params={
                "closure_start": closure_start.isoformat(),
                "closure_end": closure_end.isoformat(),
            },
            timeout=10.0,
        )
    
    async def get_pending_requests_count(self) -> int:
        """Get count of pending leave requests."""
        result = await self.get_safe(
            "/api/v1/leaves/internal/pending-count",
            default=0,
        )
        return int(result) if result else 0
    
    async def get_all_requests(
        self,
        user_id: Optional[UUID] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """Get leave requests with filters."""
        params = {}
        if user_id:
            params["user_id"] = str(user_id)
        if year:
            params["year"] = year
        if status:
            params["status"] = status
        
        return await self.get_safe(
            "/api/v1/leaves/internal/all",
            default=[],
            params=params if params else None,
        )
    
    async def get_requests_for_date(self, target_date: date) -> list[dict]:
        """Get all approved leave requests for a specific date."""
        return await self.get_safe(
            "/api/v1/leaves/internal/for-date",
            default=[],
            params={"target_date": target_date.isoformat()},
        )

    async def get_leaves_for_date(self, target_date: date) -> list[dict]:
        """Alias for get_requests_for_date for aggregator compatibility."""
        return await self.get_requests_for_date(target_date)

    async def get_leaves_in_period(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> list[dict]:
        """Get leaves in period (internal use)."""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if user_id:
            params["user_id"] = str(user_id)
        if status:
            params["status"] = status
            
        return await self.get_safe(
            "/api/v1/leaves/internal/in-period",
            default=[],
            params=params,
        )

    async def get_balance_summary(self, user_id: UUID, year: int = None) -> Optional[dict]:
        """Get comprehensive balance summary from the integrated wallet module."""
        params = {"year": year} if year else {}
        return await self.get_safe(
            f"/api/v1/leaves/wallet/{user_id}/summary",
            params=params,
        )


# Backward compatibility alias
LeavesClient = LeaveClient
