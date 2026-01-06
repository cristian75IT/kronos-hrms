"""
KRONOS Approval Service - Celery Tasks.

Background tasks for expiration handling and reminders.
"""
import logging
from datetime import datetime, timedelta

from celery import shared_task

from src.core.database import async_session_factory
from src.shared.clients import NotificationClient

logger = logging.getLogger(__name__)


@shared_task(name="approvals.check_expirations")
def check_expirations():
    """
    Check for expired approval requests and apply expiration actions.
    
    Runs every 15 minutes.
    """
    import asyncio
    asyncio.run(_check_expirations_async())


async def _check_expirations_async():
    """Async implementation of expiration check."""
    from .models import ApprovalRequest, ApprovalStatus
    from .repository import (
        ApprovalRequestRepository,
        WorkflowConfigRepository,
        ApprovalDecisionRepository,
        ApprovalHistoryRepository,
        ApprovalReminderRepository,
    )
    from .workflow_engine import WorkflowEngine
    
    async with async_session_factory() as session:
        try:
            request_repo = ApprovalRequestRepository(session)
            # Get expired requests
            now = datetime.utcnow()
            expired_requests = await request_repo.get_expiring_requests(now)
            
            if not expired_requests:
                logger.debug("No expired approval requests found")
                return
            
            logger.info(f"Found {len(expired_requests)} expired approval requests")
            
            # Initialize engine
            engine = WorkflowEngine(
                WorkflowConfigRepository(session),
                ApprovalRequestRepository(session),
                ApprovalDecisionRepository(session),
                ApprovalHistoryRepository(session),
                ApprovalReminderRepository(session),
            )
            
            # Process each expired request
            for request in expired_requests:
                try:
                    await engine.handle_expiration(request)
                    logger.info(f"Handled expiration for request {request.id}")
                except Exception as e:
                    logger.error(f"Error handling expiration for {request.id}: {e}")
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error in check_expirations: {e}")
            await session.rollback()


@shared_task(name="approvals.send_reminders")
def send_reminders():
    """
    Send reminder notifications for pending approvals.
    
    Runs every 30 minutes.
    """
    import asyncio
    asyncio.run(_send_reminders_async())


async def _send_reminders_async():
    """Async implementation of reminder sending."""
    from .models import ApprovalReminder, ApprovalRequest
    from .repository import ApprovalReminderRepository, ApprovalRequestRepository
    
    async with async_session_factory() as session:
        try:
            reminder_repo = ApprovalReminderRepository(session)
            request_repo = ApprovalRequestRepository(session)
            notification_client = NotificationClient()
            
            # Get due reminders
            now = datetime.utcnow()
            reminders = await reminder_repo.get_due_reminders(now)
            
            if not reminders:
                logger.debug("No reminders due")
                return
            
            logger.info(f"Sending {len(reminders)} approval reminders")
            
            for reminder in reminders:
                try:
                    # Get request details
                    request = await request_repo.get_by_id(reminder.approval_request_id)
                    if not request or request.status != "PENDING":
                        # Request was resolved, skip
                        await reminder_repo.mark_sent(reminder.id)
                        continue
                    
                    # Determine message based on reminder type
                    if reminder.reminder_type == "FINAL":
                        title = "⚠️ Approvazione in Scadenza!"
                        message = f"La richiesta '{request.title}' scade tra poco. Agisci subito."
                    else:
                        title = "Promemoria Approvazione"
                        message = f"Hai una richiesta in attesa: {request.title}"
                    
                    # Send notification
                    await notification_client.send_notification(
                        user_id=reminder.approver_id,
                        title=title,
                        message=message,
                        notification_type="APPROVAL_REMINDER",
                        data={
                            "approval_request_id": str(request.id),
                            "entity_type": request.entity_type,
                            "reminder_type": reminder.reminder_type,
                        },
                    )
                    
                    # Mark as sent
                    await reminder_repo.mark_sent(reminder.id)
                    logger.debug(f"Sent reminder {reminder.id} to {reminder.approver_id}")
                    
                except Exception as e:
                    logger.error(f"Error sending reminder {reminder.id}: {e}")
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error in send_reminders: {e}")
            await session.rollback()


@shared_task(name="approvals.cleanup_old_requests")
def cleanup_old_requests():
    """
    Clean up old resolved approval requests.
    
    Runs weekly. Archives requests older than configured retention period.
    """
    import asyncio
    asyncio.run(_cleanup_old_requests_async())


async def _cleanup_old_requests_async():
    """Async implementation of cleanup."""
    from .models import ApprovalRequest
    
    # Retention period: 2 years
    retention_days = 730
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    
    async with async_session_factory() as session:
        try:
            from .repository import ApprovalRequestRepository
            request_repo = ApprovalRequestRepository(session)
            
            # Count old resolved requests
            old_requests = await request_repo.get_resolved_before(cutoff)
            
            if not old_requests:
                logger.debug("No old requests to archive")
                return
            
            logger.info(f"Found {len(old_requests)} old requests to archive")
            
            # For now, just log - actual archival/deletion would be done here
            # TODO: Move to archive table or delete based on policy
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_requests: {e}")
