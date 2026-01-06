"""KRONOS Calendar Deadline Notification Scheduler.

This module provides Celery tasks for sending calendar deadline notifications.
It scans for upcoming deadlines and sends notifications to relevant users.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from celery import shared_task
from src.services.notifications.models import (
    NotificationType,
    NotificationChannel,
)
from src.services.notifications.repository import CalendarExternalRepository
from src.services.notifications.schemas import NotificationCreate
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

async def _get_async_session() -> AsyncSession:
    """Create async database session for task."""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


async def _send_notification(
    session: AsyncSession,
    user_id: UUID,
    user_email: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> None:
    """Send notification through all enabled channels."""
    from src.services.notifications.services import NotificationService
    
    service = NotificationService(session)
    
    # Send to all channels - preferences will be checked per-channel
    for channel in [NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH]:
        try:
            await service.create_notification(NotificationCreate(
                user_id=user_id,
                user_email=user_email,
                notification_type=notification_type,
                title=title,
                message=message,
                channel=channel,
                entity_type=entity_type,
                entity_id=entity_id,
                action_url=action_url,
            ))
        except Exception as e:
            print(f"[Scheduler] Error sending {channel} notification: {e}")


@shared_task(name="notifications.check_system_deadlines")
def check_system_deadlines():
    """Check for upcoming system deadlines (holidays, closures).
    
    Run this task hourly via Celery beat.
    """
    import asyncio
    asyncio.run(_check_system_deadlines_async())


async def _check_system_deadlines_async():
    """Async implementation of system deadline check."""
    session = await _get_async_session()
    
    try:
        from src.services.notifications.repository import CalendarExternalRepository
        cal_repo = CalendarExternalRepository(session)
        
        # Get deadlines in the next 24 hours
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        # Check for closures starting tomorrow
        closures = await cal_repo.get_upcoming_closures(tomorrow.date())
        
        for closure in closures:
            # Get all active users (simplified - in production, query auth service)
            await _notify_all_users_about_closure(session, closure)
        
        # Check for holidays tomorrow
        holidays = await cal_repo.get_upcoming_holidays(tomorrow.date())
        
        for holiday in holidays:
            await _notify_all_users_about_holiday(session, holiday)
        
        await session.commit()
        print(f"[Scheduler] Checked system deadlines: {len(closures)} closures, {len(holidays)} holidays")
        
    except Exception as e:
        print(f"[Scheduler] Error checking system deadlines: {e}")
        await session.rollback()
    finally:
        await session.close()


async def _notify_all_users_about_closure(session: AsyncSession, closure) -> None:
    """Send closure notification to all active users."""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/users",
                params={"is_active": True, "limit": 1000},
                timeout=30.0,
            )
            if response.status_code == 200:
                users = response.json().get("data", [])
                for user in users:
                    await _send_notification(
                        session,
                        user_id=UUID(user["id"]),
                        user_email=user["email"],
                        notification_type=NotificationType.CALENDAR_SYSTEM_DEADLINE,
                        title=f"📅 Chiusura aziendale: {closure.name}",
                        message=f"Domani, {closure.start_date.strftime('%d/%m/%Y')}: {closure.description or closure.name}",
                        action_url="/calendar",
                        entity_type="CalendarClosure",
                        entity_id=str(closure.id),
                    )
    except Exception as e:
        print(f"[Scheduler] Error notifying users about closure: {e}")


async def _notify_all_users_about_holiday(session: AsyncSession, holiday) -> None:
    """Send holiday notification to all active users."""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/users",
                params={"is_active": True, "limit": 1000},
                timeout=30.0,
            )
            if response.status_code == 200:
                users = response.json().get("data", [])
                for user in users:
                    await _send_notification(
                        session,
                        user_id=UUID(user["id"]),
                        user_email=user["email"],
                        notification_type=NotificationType.CALENDAR_SYSTEM_DEADLINE,
                        title=f"🎉 Festività: {holiday.name}",
                        message=f"Domani, {holiday.date.strftime('%d/%m/%Y')}, è festivo: {holiday.name}",
                        action_url="/calendar",
                        entity_type="CalendarHoliday",
                        entity_id=str(holiday.id),
                    )
    except Exception as e:
        print(f"[Scheduler] Error notifying users about holiday: {e}")


@shared_task(name="notifications.check_personal_deadlines")
def check_personal_deadlines():
    """Check for upcoming personal calendar events.
    
    Run this task hourly via Celery beat.
    """
    import asyncio
    asyncio.run(_check_personal_deadlines_async())


async def _check_personal_deadlines_async():
    """Async implementation of personal deadline check."""
    session = await _get_async_session()
    
    try:
        from src.services.notifications.repository import CalendarExternalRepository
        cal_repo = CalendarExternalRepository(session)
        
        now = datetime.utcnow()
        in_24_hours = now + timedelta(hours=24)
        
        # Get events starting in the next 24 hours
        events = await cal_repo.get_upcoming_personal_events(in_24_hours.date())
        
        for event in events:
            await _notify_about_personal_event(session, event)
        
        await session.commit()
        print(f"[Scheduler] Checked personal deadlines: {len(events)} events")
        
    except Exception as e:
        print(f"[Scheduler] Error checking personal deadlines: {e}")
        await session.rollback()
    finally:
        await session.close()


async def _notify_about_personal_event(session: AsyncSession, event) -> None:
    """Send personal event reminder to owner."""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/users/{event.user_id}",
                timeout=10.0,
            )
            if response.status_code == 200:
                user = response.json()
                await _send_notification(
                    session,
                    user_id=event.user_id,
                    user_email=user["email"],
                    notification_type=NotificationType.CALENDAR_PERSONAL_DEADLINE,
                    title=f"⏰ Promemoria: {event.title}",
                    message=f"Domani: {event.title}" + (f" - {event.description}" if event.description else ""),
                    action_url="/calendar",
                    entity_type="CalendarEvent",
                    entity_id=str(event.id),
                )
    except Exception as e:
        print(f"[Scheduler] Error notifying about personal event: {e}")


@shared_task(name="notifications.check_shared_deadlines")
def check_shared_deadlines():
    """Check for upcoming shared calendar events.
    
    Run this task hourly via Celery beat.
    """
    import asyncio
    asyncio.run(_check_shared_deadlines_async())


async def _check_shared_deadlines_async():
    """Async implementation of shared deadline check."""
    session = await _get_async_session()
    
    try:
        from src.services.notifications.repository import CalendarExternalRepository
        cal_repo = CalendarExternalRepository(session)
        
        now = datetime.utcnow()
        in_24_hours = now + timedelta(hours=24)
        
        # Get shared calendar events starting in the next 24 hours
        events = await cal_repo.get_upcoming_shared_events(in_24_hours.date())
        
        for event in events:
            if event.calendar_id:
                await _notify_shared_calendar_users(session, event)
        
        await session.commit()
        print(f"[Scheduler] Checked shared deadlines: {len(events)} events")
        
    except Exception as e:
        print(f"[Scheduler] Error checking shared deadlines: {e}")
        await session.rollback()
    finally:
        await session.close()


async def _notify_shared_calendar_users(session: AsyncSession, event) -> None:
    """Send notification to users who have access to the shared calendar."""
    import httpx
    
    # Get calendar shares
    from src.services.notifications.repository import CalendarExternalRepository
    cal_repo = CalendarExternalRepository(session)
    
    shares = await cal_repo.get_calendar_shares(event.calendar_id)
    
    for share in shares:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/users/{share.shared_with_user_id}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    user = response.json()
                    await _send_notification(
                        session,
                        user_id=share.shared_with_user_id,
                        user_email=user["email"],
                        notification_type=NotificationType.CALENDAR_SHARED_DEADLINE,
                        title=f"📅 Evento condiviso: {event.title}",
                        message=f"Domani: {event.title}" + (f" - {event.description}" if event.description else ""),
                        action_url="/calendar",
                        entity_type="CalendarEvent",
                        entity_id=str(event.id),
                    )
        except Exception as e:
            print(f"[Scheduler] Error notifying shared calendar user: {e}")


@shared_task(name="notifications.process_email_retries")
def process_email_retries():
    """Process retry queue for failed emails.
    
    Run this task every 5 minutes via Celery beat.
    """
    import asyncio
    asyncio.run(_process_email_retries_async())


async def _process_email_retries_async():
    """Async implementation of email retry processor."""
    from src.services.notifications.models import EmailLogStatus
    from src.services.notifications.repository import EmailLogRepository, EmailTemplateRepository
    from src.services.notifications.services import NotificationService
    
    session = await _get_async_session()
    email_repo = EmailLogRepository(session)
    template_repo = EmailTemplateRepository(session)
    service = NotificationService(session)
    
    try:
        # Get pending retries
        pending_logs = await email_repo.get_pending_retries(limit=50)
        
        if not pending_logs:
            return
            
        print(f"[Scheduler] Processing {len(pending_logs)} email retries...")
        
        for log in pending_logs:
            try:
                # Update status to processing
                log.status = EmailLogStatus.QUEUED.value
                await session.flush()
                
                # Get template
                template = await template_repo.get_by_code(log.template_code)
                if not template:
                    await email_repo.update_status(
                        log.id, 
                        EmailLogStatus.FAILED.value, 
                        error_message=f"Template {log.template_code} not found during retry"
                    )
                    await session.commit()
                    continue
                
                # Attempt resend (using internal method to avoid creating new log)
                try:
                    result = await service._send_brevo_email(
                        to_email=log.to_email,
                        to_name=log.to_name,
                        template=template,
                        variables=log.variables or {},
                    )
                    
                    # Update success
                    await email_repo.update_status(
                        log.id,
                        status=EmailLogStatus.SENT.value,
                        message_id=result.get("messageId"),
                        provider_response=result,
                    )
                    
                except Exception as e:
                    # Schedule next retry or fail permanently
                    error_msg = str(e)
                    await email_repo.update_status(
                        log.id,
                        status=EmailLogStatus.FAILED.value,
                        error_message=error_msg,
                        provider_response={"error": error_msg}
                    )
                    
                    if (log.retry_count or 0) < 3:
                        await email_repo.schedule_retry(log.id)
            
            except Exception as e:
                print(f"[Scheduler] Error processing retry for log {log.id}: {e}")
                
        await session.commit()
        
    except Exception as e:
        print(f"[Scheduler] Error in retry processor: {e}")
        await session.rollback()
    finally:
        await session.close()
