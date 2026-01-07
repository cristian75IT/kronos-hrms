"""
KRONOS - Leave Service Base Module

Contains shared dependencies and initialization logic used by all leave sub-services.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, or_
from datetime import date

from src.services.auth.models import EmployeeContract
from src.services.config.models import NationalContractVersion

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

    async def _get_saturday_rule(self, user_id: UUID, date_ref: date) -> bool:
        """Check if Saturday should be counted as leave for the user at given date."""
        try:
            # 1. Find active employee contract
            query = select(EmployeeContract).where(
                and_(
                    EmployeeContract.user_id == user_id,
                    EmployeeContract.start_date <= date_ref,
                    # Handle NULL end_date (active indefinitely)
                    # or end_date >= date_ref
                    or_(EmployeeContract.end_date.is_(None), EmployeeContract.end_date >= date_ref)
                )
            ).order_by(desc(EmployeeContract.start_date)).limit(1)
            
            contract = await self._session.scalar(query)
            if not contract or not contract.national_contract_id:
                return False
                
            # 2. Find active national contract version
            # We need the version valid at date_ref
            query_nc = select(NationalContractVersion).where(
                and_(
                    NationalContractVersion.national_contract_id == contract.national_contract_id,
                    NationalContractVersion.valid_from <= date_ref,
                    or_(NationalContractVersion.valid_to.is_(None), NationalContractVersion.valid_to >= date_ref)
                )
            ).order_by(desc(NationalContractVersion.valid_from)).limit(1)
            
            version = await self._session.scalar(query_nc)
            if version:
                return version.count_saturday_as_leave
                
            return False
        except Exception as e:
            # Log error but don't block
            print(f"Error fetching Saturday rule for user {user_id}: {e}")
            return False
