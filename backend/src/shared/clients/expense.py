"""
KRONOS - Expense Service Client

Client for inter-service communication with the Expense/Trip Service.
"""
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class ExpenseClient(BaseClient):
    """
    Client for Expense Service interactions.
    
    Used by HR Reporting service for aggregating expense data.
    """
    
    def __init__(self):
        super().__init__(
            base_url=settings.expense_service_url,
            service_name="expense",
        )
    
    async def get_pending_reports_count(self) -> int:
        """Get count of pending expense reports."""
        data = await self.get_safe("/api/v1/expenses/pending", default=[])
        return len(data) if isinstance(data, list) else 0
    
    async def get_pending_trips_count(self) -> int:
        """Get count of pending trip requests."""
        data = await self.get_safe("/api/v1/trips/pending", default=[])
        return len(data) if isinstance(data, list) else 0
    
    async def get_user_trips(
        self,
        user_id: UUID,
        year: Optional[int] = None,
    ) -> list:
        """Get trips for a user."""
        params = {}
        if year:
            params["year"] = year
        
        return await self.get_safe(
            "/api/v1/trips",
            default=[],
            params=params if params else None,
        )
    
    async def get_user_expense_reports(
        self,
        user_id: UUID,
        year: Optional[int] = None,
    ) -> list:
        """Get expense reports for a user."""
        return await self.get_safe("/api/v1/expenses", default=[])
    
    async def get_trips_for_date(self, target_date: date) -> list[dict]:
        """Get all active trips for a specific date across all users."""
        return await self.get_safe(
            "/api/v1/expenses/internal/trips-for-date",
            default=[],
            params={"target_date": target_date.isoformat()},
        )
        
    async def get_all_trips_datatable(
        self,
        draw: int,
        start: int,
        length: int,
        filters: dict,
        token: Optional[str] = None,
    ) -> dict:
        """Get all trips datatable (admin/hr view)."""
        payload = {
            "draw": draw,
            "start": start,
            "length": length,
            "search": {"value": filters.get("search"), "regex": False},
            "status": filters.get("status"),
            "date_from": filters.get("date_from"),
            "date_to": filters.get("date_to"),
        }
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        return await self.post_safe(
            "/api/v1/trips/admin/datatable",
            json=payload,
            headers=headers,
            default={"draw": draw, "recordsTotal": 0, "recordsFiltered": 0, "data": []}
        )

    async def get_all_expenses_datatable(
        self,
        draw: int,
        start: int,
        length: int,
        filters: dict,
        token: Optional[str] = None,
    ) -> dict:
        """Get all expenses datatable (admin/hr view)."""
        payload = {
            "draw": draw,
            "start": start,
            "length": length,
            "search": {"value": filters.get("search"), "regex": False},
            "status": filters.get("status"),
            "date_from": filters.get("date_from"),
            "date_to": filters.get("date_to"),
        }
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        return await self.post_safe(
            "/api/v1/expenses/admin/datatable",
            json=payload,
            headers=headers,
            default={"draw": draw, "recordsTotal": 0, "recordsFiltered": 0, "data": []}
        )
