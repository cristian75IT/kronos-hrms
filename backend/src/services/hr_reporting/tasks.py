"""
KRONOS HR Reporting Service - Celery Tasks.

Scheduled tasks for:
- Daily workforce snapshots
- Compliance checks
- Monthly stats calculation
"""
import asyncio
import logging
from datetime import date, datetime

from celery import shared_task

from src.core.database import async_session_factory, get_db_context
from src.shared.clients import AuthClient, NotificationClient
from .service import HRReportingService
from .services.timesheet import TimesheetService

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(name="hr_reporting.create_daily_snapshot")
def create_daily_snapshot():
    """
    Create daily workforce snapshot.
    
    Scheduled to run at end of each day (23:55).
    Captures key metrics for trend analysis.
    """
    logger.info("Starting daily snapshot creation")
    
    async def _create_snapshot():
        async with async_session_factory() as session:
            service = HRReportingService(session)
            try:
                snapshot = await service.create_daily_snapshot()
                await session.commit()
                logger.info(f"Daily snapshot created for {snapshot.snapshot_date}")
                return {
                    "status": "success",
                    "date": str(snapshot.snapshot_date),
                    "total_employees": snapshot.total_employees,
                    "absence_rate": float(snapshot.absence_rate),
                }
            except Exception as e:
                logger.error(f"Error creating daily snapshot: {e}")
                await session.rollback()
                return {"status": "error", "message": str(e)}
    
    return run_async(_create_snapshot())


@shared_task(name="hr_reporting.run_compliance_check")
def run_compliance_check():
    """
    Run compliance checks and create alerts.
    
    Scheduled to run daily at 8 AM.
    Checks for:
    - Vacation legal minimum not taken
    - Previous year vacation expiring (30/06)
    - Other regulatory requirements
    """
    logger.info("Starting compliance check")
    
    async def _run_check():
        async with async_session_factory() as session:
            service = HRReportingService(session)
            try:
                # Generate compliance report
                report = await service.generate_compliance_report()
                
                # Create alerts for critical issues
                alerts_created = 0
                for issue in report.issues:
                    if issue.severity == "critical":
                        await service.create_alert(
                            alert_type=issue.type,
                            title=f"Compliance: {issue.type}",
                            description=issue.description,
                            severity="critical",
                            employee_id=issue.employee_id,
                            action_required=True,
                            action_deadline=issue.deadline,
                        )
                        alerts_created += 1
                
                await session.commit()
                
                logger.info(f"Compliance check completed: {len(report.issues)} issues, {alerts_created} alerts")
                return {
                    "status": "success",
                    "issues_found": len(report.issues),
                    "alerts_created": alerts_created,
                    "compliance_rate": report.statistics.compliance_rate,
                }
            except Exception as e:
                logger.error(f"Error running compliance check: {e}")
                await session.rollback()
                return {"status": "error", "message": str(e)}
    
    return run_async(_run_check())


@shared_task(name="hr_reporting.calculate_monthly_stats")
def calculate_monthly_stats():
    """
    Calculate monthly statistics for all employees.
    
    Scheduled to run on 1st of each month.
    Pre-calculates stats for fast reporting.
    """
    today = date.today()
    # Calculate for previous month
    if today.month == 1:
        year = today.year - 1
        month = 12
    else:
        year = today.year
        month = today.month - 1
    
    logger.info(f"Starting monthly stats calculation for {year}-{month:02d}")
    
    async def _calculate_stats():
        async with async_session_factory() as session:
            service = HRReportingService(session)
            try:
                report = await service.generate_monthly_report(
                    year=year,
                    month=month,
                )
                await session.commit()
                
                logger.info(f"Monthly stats calculated: {report.employee_count} employees")
                return {
                    "status": "success",
                    "period": f"{year}-{month:02d}",
                    "employees_processed": report.employee_count,
                }
            except Exception as e:
                logger.error(f"Error calculating monthly stats: {e}")
                await session.rollback()
                return {"status": "error", "message": str(e)}
    
    return run_async(_calculate_stats())


@shared_task(name="hr_reporting.generate_report")
def generate_report_async(report_type: str, year: int, month: int = None, department_id: str = None):
    """
    Generate a report asynchronously.
    
    Can be triggered manually via admin API.
    """
    logger.info(f"Generating {report_type} report for {year}-{month or 'all'}")
    
    async def _generate():
        from uuid import UUID
        
        async with async_session_factory() as session:
            service = HRReportingService(session)
            try:
                dept_uuid = UUID(department_id) if department_id else None
                
                if report_type == "monthly":
                    report = await service.generate_monthly_report(
                        year=year,
                        month=month,
                        department_id=dept_uuid,
                    )
                elif report_type == "compliance":
                    report = await service.generate_compliance_report()
                elif report_type == "budget":
                    report = await service.generate_budget_report(
                        year=year,
                        month=month,
                    )
                else:
                    return {"status": "error", "message": f"Unknown report type: {report_type}"}
                
                await session.commit()
                
                return {
                    "status": "success",
                    "report_type": report_type,
                    "period": f"{year}-{month:02d}" if month else str(year),
                }
            except Exception as e:
                logger.error(f"Error generating report: {e}")
                await session.rollback()
                return {"status": "error", "message": str(e)}
    
    return run_async(_generate())


@shared_task(name="hr_reporting.update_timesheets")
def update_daily_timesheets():
    """
    Daily task to update all employee timesheets.

    Runs daily (e.g., 02:00) to keep timesheets up-to-date.
    """
    async def _update_all_timesheets():
        today = date.today()
        logger.info(f"Starting daily timesheet update for {today}")
        
        auth_client = AuthClient()
        
        try:
            # 1. Get all active users
            users = await auth_client.get_users()
            active_users = [u for u in users if u.get("is_active", True)]
            logger.info(f"Found {len(active_users)} active users")
            
            async with get_db_context() as session:
                service = TimesheetService(session)
                
                for user in active_users:
                    try:
                        user_id = UUID(user["id"])
                        # Update current month
                        await service.update_timesheet_data(
                            user_id, 
                            today.year, 
                            today.month
                        )
                    except Exception as e:
                        logger.error(f"Failed to update timesheet for user {user.get('id')}: {e}")
                        
            logger.info("Daily timesheet update completed")
            
        except Exception as e:
            logger.error(f"Critical error in daily timesheet update: {e}")

    return run_async(_update_all_timesheets())


@shared_task(name="hr_reporting.check_timesheet_deadlines")
def check_timesheet_deadlines():
    """
    Check for approaching timesheet deadlines and send reminders.
    
    Runs daily (e.g., 08:00).
    """
    async def _check_deadlines():
        today = date.today()
        logger.info(f"Checking timesheet deadlines for {today}")
        
        async with get_db_context() as session:
            service = TimesheetService(session)
            notification = NotificationClient()
            
            # Check deadline for previous month
            # Logic: If today is close to deadline, find unconfirmed timesheets
            # We need to know the deadline for the "Timesheet Month"
            # If today is Jan 24, we are checking Dec timesheet deadline (e.g. Jan 27)
            
            # Find relevant year/month. 
            # We assume we are checking the "previous valid month" for confirmation.
            # E.g. If today is Jan, we check Dec.
            if today.month == 1:
                chk_year = today.year - 1
                chk_month = 12
            else:
                chk_year = today.year
                chk_month = today.month - 1
                
            can_confirm, deadline = await service.check_confirmation_window(chk_year, chk_month)
            
            if not can_confirm and today > deadline:
                logger.info("Confirmation window already closed. Skipping reminders.")
                return

            days_until = (deadline - today).days
            
            # Remind on: 5 days before, 2 days before, 0 days (Deadline)
            if days_until not in [5, 2, 0]:
                return

            logger.info(f"Deadline approaching in {days_until} days ({deadline}). Sending reminders.")
            
            # Get all active users
            auth = AuthClient()
            users = await auth.get_users()
            
            for user in users:
                if not user.get("is_active", True):
                    continue
                    
                user_id = UUID(user["id"])
                ts = await service.get_or_create_timesheet(user_id, chk_year, chk_month)
                
                if ts.status in ["DRAFT", "PENDING"]:  # Uses string/enum value
                    # SEND REMINDER
                    try:
                        title = "⚠️ Scadenza Timesheet"
                        msg = f"Il timesheet di {chk_month}/{chk_year} scade il {deadline.strftime('%d/%m/%Y')}. Conferalo ora."
                        if days_until == 0:
                            title = "🚨 ULTIMO GIORNO: Timesheet"
                            msg = f"Oggi scade la conferma del timesheet di {chk_month}/{chk_year}. Conferalo urgentemente."
                            
                        await notification.send_notification(
                            user_id=user_id,
                            notification_type="TIMESHEET_REMINDER",
                            title=title,
                            message=msg,
                            action_url="/timesheet",
                            priority="high" if days_until == 0 else "normal"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send reminder to {user_id}: {e}")

    return run_async(_check_deadlines())
