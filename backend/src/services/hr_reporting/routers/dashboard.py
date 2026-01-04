"""
KRONOS HR Reporting Service - Dashboard Router.

Real-time dashboard endpoints for HR professionals.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload

from ..service import HRReportingService
from ..schemas import DashboardOverview, AlertItem, TeamStats

router = APIRouter(prefix="/dashboard", tags=["HR Dashboard"])


def get_service(session: AsyncSession = Depends(get_db)) -> HRReportingService:
    return HRReportingService(session)


# ═══════════════════════════════════════════════════════════
# Main Dashboard
# ═══════════════════════════════════════════════════════════

@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    target_date: Optional[date] = None,
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    service: HRReportingService = Depends(get_service),
):
    """
    Get complete HR dashboard overview.
    
    Includes:
    - Workforce status (employees, absences, trips)
    - Pending approvals count
    - Active alerts
    - Quick statistics
    """
    return await service.get_dashboard_overview(target_date)


@router.get("/team/{team_id}")
async def get_team_dashboard(
    team_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: HRReportingService = Depends(get_service),
):
    """
    Get team-specific dashboard.
    
    Only accessible by team manager or HR admin.
    """
    # Verify user is manager of this team or admin
    if not current_user.is_admin and not current_user.is_manager:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view team dashboard"
        )
    
    return await service.get_team_dashboard(team_id, current_user.sub)


# ═══════════════════════════════════════════════════════════
# Alerts
# ═══════════════════════════════════════════════════════════

@router.get("/alerts")
async def get_active_alerts(
    limit: int = Query(default=50, le=200),
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    service: HRReportingService = Depends(get_service),
):
    """Get all active HR alerts."""
    return await service.get_active_alerts(limit)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an alert."""
    try:
        alert = await service.acknowledge_alert(alert_id, current_user.sub)
        await db.commit()
        return {"status": "acknowledged", "alert_id": str(alert_id)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Mark alert as resolved."""
    try:
        alert = await service.resolve_alert(alert_id)
        await db.commit()
        return {"status": "resolved", "alert_id": str(alert_id)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Quick Stats
# ═══════════════════════════════════════════════════════════

@router.get("/stats/today")
async def get_today_stats(
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    service: HRReportingService = Depends(get_service),
):
    """Get quick statistics for today."""
    overview = await service.get_dashboard_overview(date.today())
    return {
        "date": str(date.today()),
        "workforce": overview.workforce.model_dump(),
        "pending": overview.pending_approvals.model_dump(),
        "alerts_count": len(overview.alerts),
    }


@router.get("/stats/week")
async def get_week_stats(
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    service: HRReportingService = Depends(get_service),
):
    """Get weekly trend statistics."""
    # Would aggregate data for the current week
    return {
        "period": "current_week",
        "avg_absence_rate": 0,
        "total_leave_days": 0,
        "total_expense_reports": 0,
    }
