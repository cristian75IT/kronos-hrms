"""
KRONOS Approvals Service - Base Module.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.clients import AuthClient, NotificationClient
from src.shared.audit_client import get_audit_logger
from src.services.approvals.repository import (
    WorkflowConfigRepository,
    ApprovalRequestRepository,
    ApprovalDecisionRepository,
    ApprovalHistoryRepository,
    ApprovalReminderRepository
)
from src.services.approvals.workflow_engine import WorkflowEngine

class BaseApprovalService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._config_repo = WorkflowConfigRepository(session)
        self._request_repo = ApprovalRequestRepository(session)
        self._decision_repo = ApprovalDecisionRepository(session)
        self._history_repo = ApprovalHistoryRepository(session)
        self._reminder_repo = ApprovalReminderRepository(session)
        
        self._engine = WorkflowEngine(
            self._config_repo,
            self._request_repo,
            self._decision_repo,
            self._history_repo,
            self._reminder_repo
        )
        
        self._auth_client = AuthClient()
        self._notification_client = NotificationClient()
        self._audit = get_audit_logger("approval-service")
