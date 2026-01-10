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
        "src.services.hr_reporting.tasks",
        "background_jobs.tasks.reconciliation",
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
        # ─────────────────────────────────────────────────────────────
        # HR Reporting Tasks
        # ─────────────────────────────────────────────────────────────
        # Daily workforce snapshot - runs at 23:55 (end of day)
        "hr-daily-snapshot": {
            "task": "hr_reporting.create_daily_snapshot",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "reporting"},
        },
        # Compliance check - runs daily at 8 AM
        "hr-compliance-check": {
            "task": "hr_reporting.run_compliance_check",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "reporting"},
        },
        # Monthly stats calculation - runs on 1st of each month at 6 AM
        "hr-monthly-stats": {
            "task": "hr_reporting.calculate_monthly_stats",
            "schedule": 2592000.0,  # Monthly (30 days)
            "options": {"queue": "reporting"},
        },
        # Daily Timesheet Update - runs at 02:00 AM
        "hr-daily-timesheet-update": {
            "task": "hr_reporting.update_timesheets",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "reporting"},
        },
        # Timesheet Deadline Check - runs daily at 09:00 AM
        "hr-timesheet-deadline-check": {
            "task": "hr_reporting.check_timesheet_deadlines",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "reporting"},
        },
        # ─────────────────────────────────────────────────────────────
        # Balance Reconciliation Tasks
        # ─────────────────────────────────────────────────────────────
        # Daily reconciliation - runs at 2 AM
        "balance-reconciliation": {
            "task": "reconciliation.check_balance_consistency",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "maintenance"},
        },
    },
)

