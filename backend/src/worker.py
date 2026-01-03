"""KRONOS Celery Worker Configuration.

This module defines the Celery application instance shared across services.
"""
from celery import Celery
from src.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "kronos_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Auto-discover tasks from all services
    imports=[
        "src.services.notifications.tasks",
        "src.services.audit.tasks",
        # Add other service tasks here as needed
    ],
    # Cron tasks (Beat)
    beat_schedule={
        "check-system-deadlines": {
            "task": "notifications.check_system_deadlines",
            "schedule": 3600.0,  # Hourly
        },
        "check-personal-deadlines": {
            "task": "notifications.check_personal_deadlines",
            "schedule": 3600.0,  # Hourly
        },
        "check-shared-deadlines": {
            "task": "notifications.check_shared_deadlines",
            "schedule": 3600.0,  # Hourly
        },
        "process-email-retries": {
            "task": "notifications.process_email_retries",
            "schedule": 300.0,   # Every 5 minutes
        },
        # Audit Data Retention - runs daily at 3 AM
        "audit-archive-old-logs": {
            "task": "audit.archive_old_logs",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "maintenance"},
        },
        # Audit Stats Refresh - runs every 6 hours
        "audit-refresh-stats": {
            "task": "audit.refresh_daily_stats",
            "schedule": 21600.0,  # Every 6 hours
        },
    },
)

