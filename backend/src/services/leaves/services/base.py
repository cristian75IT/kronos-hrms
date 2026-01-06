"""
KRONOS - Leave Service Base Module

Contains shared dependencies and initialization logic used by all leave sub-services.
"""
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import (
    NotFoundError,
    ConflictError,
    BusinessRuleError,
    ValidationError,
)
from src.services.leaves.repository import (
    LeaveRequestRepository,
    LeaveInterruptionRepository,
    ApprovalDelegationRepository,
)
from src.services.leaves.policy_engine import PolicyEngine
from src.services.leaves.calendar_utils import CalendarUtils
from src.services.leaves.balance_service import LeaveBalanceService
from src.services.leaves.notification_handler import LeaveNotificationHandler
from src.shared.audit_client import get_audit_logger

if TYPE_CHECKING:
    from src.shared.clients import (
        AuthClient,
        ConfigClient,
        LeavesWalletClient,
        ApprovalClient,
    )


class BaseLeaveService:
    """
    Base class for leave service modules.
    
    Provides shared dependencies and initialization for:
    - Database session and repository
    - External service clients (auth, config, wallet, approval)
    - Audit logging
    - Notification handler
    - Balance service
    - Policy engine
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._request_repo = LeaveRequestRepository(session)
        self._interruption_repo = LeaveInterruptionRepository(session)
        self._delegation_repo = ApprovalDelegationRepository(session)
        
        # Audit logging
        self._audit = get_audit_logger("leave-service")
        
        # Initialize clients (lazy import to avoid circular dependencies)
        from src.shared.clients import (
            AuthClient,
            ConfigClient,
            LeavesWalletClient as WalletClient,
            ApprovalClient,
        )
        self._auth_client = AuthClient()
        self._config_client = ConfigClient()
        self._wallet_client = WalletClient()
        self._approval_client = ApprovalClient()
        
        # Notification handler
        self._notifier = LeaveNotificationHandler()
        
        # Utility services
        self._calendar_utils = CalendarUtils(self._config_client)
        self._balance_service = LeaveBalanceService(session, self._wallet_client)
        
        # Policy engine
        self._policy_engine = PolicyEngine(
            session,
            self._request_repo,
            self._balance_service,
            config_client=self._config_client,
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Common Helper Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _get_user_info(self, user_id: UUID) -> Optional[dict]:
        """Get user info from auth service."""
        return await self._auth_client.get_user_info(user_id)
    
    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        return await self._auth_client.get_user_email(user_id)
    
    async def _get_subordinates(self, manager_id: UUID) -> list[UUID]:
        """Get subordinate user IDs from auth service."""
        return await self._auth_client.get_subordinates(manager_id)
