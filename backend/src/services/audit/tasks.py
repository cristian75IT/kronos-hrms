"""KRONOS Audit Service - Celery Tasks.

Scheduled tasks for audit log maintenance and statistics.
"""
import asyncio
import logging
from celery import shared_task

from src.core.database import get_db_context

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(name="audit.archive_old_logs", bind=True, max_retries=3)
def archive_old_logs(self, retention_days: int = 90):
    """
    Archive audit logs older than retention_days.
    
    Runs daily to move old logs to archive tables.
    Default retention: 90 days (configurable).
    """
    async def _archive():
        from sqlalchemy import text
        
        async with get_db_context() as session:
            result = await session.execute(
                text("SELECT audit.archive_old_logs(:days)"),
                {"days": retention_days}
            )
            archived_count = result.scalar() or 0
            await session.commit()
            return archived_count
    
    try:
        archived_count = run_async(_archive())
        logger.info(f"Audit archive completed: {archived_count} logs archived (retention: {retention_days} days)")
        return {"archived_count": archived_count, "retention_days": retention_days}
        
    except Exception as e:
        logger.error(f"Audit archive failed: {e}")
        self.retry(exc=e, countdown=60 * 5)  # Retry in 5 minutes


@shared_task(name="audit.refresh_daily_stats", bind=True, max_retries=3)
def refresh_daily_stats(self):
    """
    Refresh the materialized view for daily audit statistics.
    
    Runs every 6 hours to keep dashboard stats current.
    """
    async def _refresh():
        from sqlalchemy import text
        
        async with get_db_context() as session:
            try:
                await session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY audit.audit_daily_stats"))
                await session.commit()
                return {"mode": "concurrent"}
            except Exception:
                # Fallback to non-concurrent refresh
                await session.execute(text("REFRESH MATERIALIZED VIEW audit.audit_daily_stats"))
                await session.commit()
                return {"mode": "fallback"}
    
    try:
        result = run_async(_refresh())
        logger.info(f"Audit daily stats materialized view refreshed ({result['mode']})")
        return {"status": "success", **result}
        
    except Exception as e:
        logger.error(f"Audit stats refresh failed: {e}")
        self.retry(exc=e, countdown=60 * 5)


@shared_task(name="audit.purge_old_archives", bind=True, max_retries=3)
def purge_old_archives(self, archive_retention_days: int = 365):
    """
    Purge archived audit logs older than archive_retention_days.
    
    Runs monthly (manually triggered or scheduled) for GDPR compliance.
    Default archive retention: 365 days.
    """
    async def _purge():
        from sqlalchemy import text
        
        async with get_db_context() as session:
            result = await session.execute(
                text("SELECT audit.purge_archives(:days)"),
                {"days": archive_retention_days}
            )
            purged_count = result.scalar() or 0
            await session.commit()
            return purged_count
    
    try:
        purged_count = run_async(_purge())
        logger.info(f"Audit archive purge completed: {purged_count} records purged (retention: {archive_retention_days} days)")
        return {"purged_count": purged_count, "archive_retention_days": archive_retention_days}
        
    except Exception as e:
        logger.error(f"Audit archive purge failed: {e}")
        self.retry(exc=e, countdown=60 * 5)
