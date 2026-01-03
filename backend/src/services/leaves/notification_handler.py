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

    # ═══════════════════════════════════════════════════════════
    # Voluntary Work Notifications
    # ═══════════════════════════════════════════════════════════

    async def notify_voluntary_work_request(self, request: LeaveRequest, interruption):
        """Notify manager about employee's request to work during vacation."""
        # Get the manager from the request (would need to fetch from auth service)
        # For now, we use a placeholder
        try:
            await self._client.send_notification(
                user_id=request.approved_by or request.user_id,  # Fallback to user if no approver
                notification_type="voluntary_work_request",
                title="Richiesta lavoro volontario",
                message=(
                    f"Il dipendente ha richiesto di lavorare durante le ferie approvate "
                    f"({request.start_date.strftime('%d/%m/%Y')} - {request.end_date.strftime('%d/%m/%Y')}). "
                    f"Giorni richiesti: {len(interruption.specific_days or [])}. "
                    f"Motivo: {interruption.reason}"
                ),
                entity_type="LeaveInterruption",
                entity_id=str(interruption.id),
            )
        except Exception:
            pass  # Non-critical notification

    async def notify_voluntary_work_approved(self, request: LeaveRequest, interruption):
        """Notify employee that their voluntary work request was approved."""
        work_days = interruption.specific_days or []
        days_display = ", ".join(work_days[:3])
        if len(work_days) > 3:
            days_display += f" (+{len(work_days) - 3} altri)"
        
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="voluntary_work_approved",
            title="Richiesta lavoro approvata",
            message=(
                f"La tua richiesta di lavorare durante le ferie è stata approvata. "
                f"Giorni: {days_display}. "
                f"I giorni di ferie ({interruption.days_refunded}) sono stati riaccreditati al tuo saldo."
            ),
            entity_type="LeaveInterruption",
            entity_id=str(interruption.id),
        )

    async def notify_voluntary_work_rejected(self, request: LeaveRequest, interruption, reason: str):
        """Notify employee that their voluntary work request was rejected."""
        await self._client.send_notification(
            user_id=request.user_id,
            notification_type="voluntary_work_rejected",
            title="Richiesta lavoro rifiutata",
            message=(
                f"La tua richiesta di lavorare durante le ferie è stata rifiutata. "
                f"Motivo: {reason}. "
                f"Le tue ferie rimangono secondo il piano originale approvato."
            ),
            entity_type="LeaveInterruption",
            entity_id=str(interruption.id),
        )

