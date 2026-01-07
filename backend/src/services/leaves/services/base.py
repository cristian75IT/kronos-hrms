"""
KRONOS - Leave Service Base Module

Contains shared dependencies and initialization logic used by all leave sub-services.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.leaves.repository import (
    LeaveRequestRepository,
    LeaveInterruptionRepository,
    ApprovalDelegationRepository,
)
from src.services.leaves.policy_engine import PolicyEngine
from src.services.leaves.calendar_utils import CalendarUtils
from src.services.leaves.balance_service import LeaveBalanceService
from src.services.leaves.notification_handler import LeaveNotificationHandler
from src.services.leaves.ledger import TimeLedgerService
from src.shared.audit_client import get_audit_logger
from src.shared.clients import AuthClient, ConfigClient, ApprovalClient


class BaseLeaveService:
    """
    Base class for leave service modules.
    
    Provides shared dependencies and initialization for:
    - Database session and repository
    - External service clients (auth, config, approval)
    - Local wallet service (no HTTP calls)
    - Time Ledger service (enterprise ledger)
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
        
        # External service clients (still HTTP-based)
        self._auth_client = AuthClient()
        self._config_client = ConfigClient()
        self._approval_client = ApprovalClient()
        
        # Notification handler
        self._notifier = LeaveNotificationHandler()
        
        # Utility services (now with local wallet)
        self._calendar_utils = CalendarUtils(self._config_client)
        self._balance_service = LeaveBalanceService(session)
        
        # Enterprise Ledger Service (new)
        self._ledger_service = TimeLedgerService(session)
        
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
