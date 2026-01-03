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

from src.core.database import async_session_factory
from .service import HRReportingService

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
