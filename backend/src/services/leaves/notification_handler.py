from datetime import date
from decimal import Decimal
from uuid import UUID

from src.shared.clients import NotificationClient
from src.services.leaves.models import LeaveRequest

class LeaveNotificationHandler:
    """Handles logic for sending leave-related notifications."""
    
    def __init__(self):
        self._client = NotificationClient()

    async def notify_submission(self, request: LeaveRequest):
        """Notify user that request was submitted."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="leave_request_submitted",
            title="Richiesta ferie sottomessa",
            message=f"Richiesta {request.leave_type_code} dal {request.start_date.strftime('%d/%m/%Y')} sottomessa",
            entity_type="LeaveRequest",
            entity_id=str(request.id),
        )

    async def notify_approved(self, request: LeaveRequest):
        """Notify user that request was approved."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="leave_request_approved",
            title="Richiesta approvata",
            message=f"La tua richiesta {request.leave_type_code} è stata approvata",
            entity_type="LeaveRequest",
            entity_id=str(request.id),
        )

    async def notify_conditional_approval(self, request: LeaveRequest, condition_details: str):
        """Notify user of validation conditions."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="leave_conditional_approval",
            title="Approvazione condizionale",
            message=f"La tua richiesta è stata approvata con condizioni: {condition_details}",
            entity_type="LeaveRequest",
            entity_id=str(request.id),
        )

    async def notify_rejected(self, request: LeaveRequest, reason: str):
        """Notify user that request was rejected."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="leave_request_rejected",
            title="Richiesta rifiutata",
            message=f"La tua richiesta {request.leave_type_code} è stata rifiutata: {reason}",
            entity_type="LeaveRequest",
            entity_id=str(request.id),
        )

    async def notify_revoked(self, request: LeaveRequest, reason: str):
        """Notify user that approval was revoked."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="leave_approval_revoked",
            title="Approvazione revocata",
            message=f"L'approvazione per la tua richiesta {request.leave_type_code} è stata revocata: {reason}",
            entity_type="LeaveRequest",
            entity_id=str(request.id),
        )

    async def notify_reopened(self, request: LeaveRequest):
        """Notify user that request was reopened."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="leave_request_reopened",
            title="Richiesta riaperta",
            message=f"La tua richiesta {request.leave_type_code} è stata riaperta per revisione",
            entity_type="LeaveRequest",
            entity_id=str(request.id),
        )

    async def notify_recalled(self, request: LeaveRequest, reason: str, recall_date: date, days_used: Decimal, days_to_restore: Decimal):
        """Notify user that they have been recalled (Richiamo in Servizio)."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="leave_request_recalled",
            title="Richiamo in Servizio",
            message=(
                f"Sei stato richiamato dal periodo di ferie per: {reason}. "
                f"Data rientro: {recall_date.strftime('%d/%m/%Y')}. "
                f"Giorni goduti: {days_used}. Giorni da recuperare: {days_to_restore}. "
                f"Hai diritto a riprogrammare i giorni non goduti e alla compensazione prevista dal CCNL."
            ),
            entity_type="LeaveRequest",
            entity_id=str(request.id),
        )
