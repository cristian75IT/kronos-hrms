"""
KRONOS - Auth Service Client

Provides access to user management, organization structure, and authentication data.
"""
import logging
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class AuthClient(BaseClient):
    """Client for Auth Service interactions."""
    
    def __init__(self):
        super().__init__(
            base_url=settings.auth_service_url,
            service_name="auth",
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # User Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_user_info(self, user_id: UUID) -> Optional[dict]:
        """Get user details from auth service."""
        return await self.get_safe(f"/api/v1/users/{user_id}")
    
    async def get_user(self, user_id: UUID) -> Optional[dict]:
        """Alias for get_user_info for aggregator compatibility."""
        return await self.get_user_info(user_id)
    
    async def get_users(self, active_only: bool = True) -> list[dict]:
        """Get all users from auth service."""
        result = await self.get_safe(
            "/api/v1/users/internal/all",
            default=[],
            params={"active_only": active_only},
        )
        return result if isinstance(result, list) else []
    
    async def get_users_by_role(self, role_id: UUID) -> list[dict]:
        """Get users with specific role ID."""
        result = await self.get_safe(
            f"/api/v1/users/internal/by-role/{role_id}",
            default=[],
        )
        return result if isinstance(result, list) else []

    async def get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email."""
        user = await self.get_user_info(user_id)
        return user.get("email") if user else None
    
    async def get_subordinates(self, manager_id: UUID) -> list[UUID]:
        """Get subordinates for a manager."""
        data = await self.get_safe(
            f"/api/v1/users/subordinates/{manager_id}",
            default=[],
        )
        try:
            return [UUID(u["id"]) for u in data if u.get("id")]
        except (ValueError, TypeError):
            return []
    
    async def get_employee_trainings(self, user_id: UUID) -> list[dict]:
        """Get safety training records for an employee."""
        return await self.get_safe(
            f"/api/v1/users/{user_id}/trainings",
            default=[],
        )
    
    async def get_approvers(self) -> list[dict]:
        """Get all approvers (internal use, no auth required)."""
        return await self.get_safe(
            "/api/v1/users/internal/approvers",
            default=[],
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Organization Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_department(self, department_id: UUID) -> Optional[dict]:
        """Get department details including manager_id."""
        return await self.get_safe(
            f"/api/v1/organization/departments/{department_id}"
        )
    
    async def get_service(self, service_id: UUID) -> Optional[dict]:
        """Get service details including coordinator_id."""
        return await self.get_safe(
            f"/api/v1/organization/services/{service_id}"
        )
