from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import require_hr, require_permission, TokenPayload
from src.services.leaves.report_service import LeaveReportService
from src.services.leaves.schemas import (
    DailyAttendanceRequest,
    DailyAttendanceResponse,
    AggregateReportRequest,
    AggregateReportResponse,
)
from src.services.leaves.deps import get_report_service

router = APIRouter()

# ═══════════════════════════════════════════════════════════
# Report Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/leaves/daily-attendance", response_model=DailyAttendanceResponse)
async def get_daily_attendance(
    request: DailyAttendanceRequest,
    token: TokenPayload = Depends(require_permission("reports:view")),
    service: LeaveReportService = Depends(get_report_service),
):
    """Get daily attendance report for HR."""
    return await service.get_daily_attendance(request)

@router.post("/leaves/aggregate-attendance", response_model=AggregateReportResponse)
async def get_aggregate_attendance(
    request: AggregateReportRequest,
    token: TokenPayload = Depends(require_permission("reports:view")),
    service: LeaveReportService = Depends(get_report_service),
):
    """Get aggregated attendance report for HR."""
    return await service.get_aggregate_report(request)
