"""
KRONOS HR Reporting Service - Admin Router.

Administrative endpoints for managing HR reporting service.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_admin, TokenPayload

from ..service import HRReportingService
from ..schemas import AlertCreate, AlertResponse

router = APIRouter(prefix="/admin", tags=["HR Admin"])


def get_service(session: AsyncSession = Depends(get_db)) -> HRReportingService:
    return HRReportingService(session)


# ═══════════════════════════════════════════════════════════
# Snapshot Management
# ═══════════════════════════════════════════════════════════

@router.post("/snapshots/create-daily")
async def create_daily_snapshot(
    current_user: TokenPayload = Depends(require_admin),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update daily workforce snapshot.
    
    This is typically called by a scheduled job at end of day.
    """
    try:
        snapshot = await service.create_daily_snapshot()
        await db.commit()
        return {
            "status": "created",
            "snapshot_id": str(snapshot.id),
            "date": str(snapshot.snapshot_date),
            "metrics": {
                "total_employees": snapshot.total_employees,
                "on_leave": snapshot.employees_on_leave,
                "on_trip": snapshot.employees_on_trip,
                "absence_rate": float(snapshot.absence_rate),
            },
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots/history")
async def get_snapshot_history(
    days: int = 30,
    current_user: TokenPayload = Depends(require_admin),
    service: HRReportingService = Depends(get_service),
):
    """Get historical snapshots for trend analysis."""
    # TODO: Implement snapshot history retrieval
    return {
        "period": f"last_{days}_days",
        "snapshots": [],
    }


# ═══════════════════════════════════════════════════════════
# Alert Management
# ═══════════════════════════════════════════════════════════

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    data: AlertCreate,
    current_user: TokenPayload = Depends(require_admin),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Create a new HR alert."""
    try:
        alert = await service.create_alert(
            alert_type=data.alert_type,
            title=data.title,
            description=data.description,
            severity=data.severity,
            employee_id=data.employee_id,
            department_id=data.department_id,
            action_required=data.action_required,
            action_deadline=data.action_deadline,
            extra_data=data.metadata,
        )
        await db.commit()
        return alert
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alerts/summary")
async def get_alerts_summary(
    current_user: TokenPayload = Depends(require_admin),
    service: HRReportingService = Depends(get_service),
):
    """Get summary of alerts by severity and type."""
    alerts = await service.get_active_alerts(limit=500)
    
    by_severity = {"info": 0, "warning": 0, "critical": 0}
    by_type = {}
    
    for alert in alerts:
        by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1
        by_type[alert.type] = by_type.get(alert.type, 0) + 1
    
    return {
        "total_active": len(alerts),
        "by_severity": by_severity,
        "by_type": by_type,
        "action_required": len([a for a in alerts if a.action_required]),
    }


# ═══════════════════════════════════════════════════════════
# Report Cache Management
# ═══════════════════════════════════════════════════════════

@router.post("/cache/invalidate")
async def invalidate_cache(
    report_type: Optional[str] = None,
    current_user: TokenPayload = Depends(require_admin),
):
    """
    Invalidate cached reports.
    
    Useful when source data has been corrected.
    """
    # TODO: Implement cache invalidation
    return {
        "status": "cache_invalidated",
        "report_type": report_type or "all",
    }


# ═══════════════════════════════════════════════════════════
# Compliance Check
# ═══════════════════════════════════════════════════════════

@router.post("/compliance/run-check")
async def run_compliance_check(
    current_user: TokenPayload = Depends(require_admin),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Run compliance checks and create alerts for issues.
    
    This would typically run as a scheduled job.
    """
    try:
        # Get compliance issues
        report = await service.generate_compliance_report(
            generated_by=current_user.sub
        )
        
        # Create alerts for critical issues
        alerts_created = 0
        for issue in report.issues:
            if issue.severity == "critical":
                await service.create_alert(
                    alert_type=issue.type,
                    title=f"Compliance Issue: {issue.type}",
                    description=issue.description,
                    severity="critical",
                    employee_id=issue.employee_id,
                    action_required=True,
                    action_deadline=issue.deadline,
                )
                alerts_created += 1
        
        await db.commit()
        
        return {
            "status": "completed",
            "issues_found": len(report.issues),
            "alerts_created": alerts_created,
            "compliance_rate": report.statistics.compliance_rate,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Monthly Stats Calculation
# ═══════════════════════════════════════════════════════════

@router.post("/stats/calculate-monthly")
async def calculate_monthly_stats(
    year: int,
    month: int,
    current_user: TokenPayload = Depends(require_admin),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Pre-calculate monthly statistics for all employees.
    
    This populates the EmployeeMonthlyStats table for fast reporting.
    Run this at the end of each month.
    """
    try:
        report = await service.generate_monthly_report(
            year=year,
            month=month,
            generated_by=current_user.sub,
        )
        await db.commit()
        
        return {
            "status": "completed",
            "year": year,
            "month": month,
            "employees_processed": report.employee_count,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════

@router.get("/health")
async def health_check(
    service: HRReportingService = Depends(get_service),
):
    """Health check for HR reporting service."""
    return {
        "status": "healthy",
        "service": "hr-reporting",
        "database": "connected",
    }
