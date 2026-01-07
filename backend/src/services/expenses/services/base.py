"""
KRONOS - Expenses Service Base

Shared dependencies and utilities for Expenses sub-services.
"""
import logging
from typing import Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.audit_client import get_audit_logger
from src.shared.clients import (
    AuthClient, 
    ConfigClient, 
    NotificationClient, 
    ApprovalClient
)

from src.services.expenses.repository import (
    BusinessTripRepository,
    DailyAllowanceRepository,
    ExpenseReportRepository,
    ExpenseItemRepository,
)
        # Local Services
        # self._wallet_service = TripWalletService(session)  # Removed legacy wallet

        
        # Enterprise Ledger Service (new)
        self._ledger_service = ExpenseLedgerService(session)
        
        # Shared Clients
        self._auth_client = AuthClient()
        self._config_client = ConfigClient()
        self._notifications = NotificationClient()
        self._approval_client = ApprovalClient()

    @property
    def db(self) -> AsyncSession:
        return self._session

    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        return await self._auth_client.get_user_email(user_id)

    async def _send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        entity_type: str = None,
        entity_id: str = None,
    ) -> None:
        """Send notification via notification-service."""
        try:
            await self._notifications.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                entity_type=entity_type,
                entity_id=entity_id
            )
        except Exception as e:
            logger.warning(f"Failed to send notification to {user_id}: {e}")

    async def _get_expense_type(self, expense_type_id: UUID) -> Optional[dict]:
        """Get expense type from config service."""
        try:
            types = await self._config_client.get_expense_types()
            for t in types:
                if t.get("id") == str(expense_type_id):
                    return t
        except Exception as e:
            logger.warning(f"Failed to fetch expense type {expense_type_id}: {e}")
        return None

    def _map_expense_category(self, code: str) -> str:
        """Map internal expense type codes to wallet categories."""
        mapping = {
            "VIT": "FOOD",
            "ALL": "HOTEL",
            "TRA": "TRANSPORT",
            "AUT": "TRANSPORT",
            "PAR": "TRANSPORT",
            "TEL": "COMMUNICATION",
            "DIV": "OTHER"
        }
        return mapping.get(code, "OTHER")
