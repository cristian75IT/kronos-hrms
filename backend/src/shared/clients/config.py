"""
KRONOS - Config Service Client

Provides access to system configuration, holidays, closures, and leave types.
"""
import logging
from datetime import date
from typing import Optional, Any
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class ConfigClient(BaseClient):
    """Client for Config Service interactions."""
    
    def __init__(self):
        super().__init__(
            base_url=settings.config_service_url,
            service_name="config",
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Holiday & Closure Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_holidays(
        self,
        year: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """
        Get holidays for a year.
        
        Note: For calendar integration, prefer CalendarClient.get_holidays()
        """
        params = {"year": year}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        data = await self.get_safe("/api/v1/holidays", default=[], params=params)
        
        # Handle both list and paginated responses
        if isinstance(data, dict):
            return data.get("items", [])
        return data if isinstance(data, list) else []
    
    async def get_company_closures(self, year: int) -> list[dict]:
        """
        Get company closures for a year.
        
        Note: For calendar integration, prefer CalendarClient.get_closures()
        """
        data = await self.get_safe(
            "/api/v1/closures",
            default={},
            params={"year": year},
        )
        
        if isinstance(data, dict):
            return data.get("items", [])
        return []
    
    # ═══════════════════════════════════════════════════════════════════════
    # Configuration Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_expense_types(self) -> list[dict]:
        """Get all expense types."""
        return await self.get_safe("/api/v1/expense-types", default=[])
    
    async def get_sys_config(self, key: str, default: Any = None) -> Any:
        """Get system config value by key."""
        data = await self.get_safe(f"/api/v1/config/{key}")
        if data and isinstance(data, dict):
            return data.get("value", default)
        return default
    
    async def get_leave_type(self, leave_type_id: UUID) -> Optional[dict]:
        """Get leave type details."""
        return await self.get_safe(f"/api/v1/leave-types/{leave_type_id}")
