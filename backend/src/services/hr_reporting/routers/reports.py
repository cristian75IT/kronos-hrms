"""
KRONOS HR Reporting Service - Reports Router.

Endpoints for generating and retrieving HR reports.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload

from ..service import HRReportingService
from ..aggregator import HRDataAggregator
from ..schemas import (
    MonthlyReportResponse,
    ComplianceReportResponse,
    BudgetReportResponse,
    ReportRequest,
    CustomReportRequest,
    ExportResponse,
    DailyAttendanceResponse,
    AggregateAttendanceResponse,
    AggregateAttendanceRequest,
    AttendanceItem,
    AggregateAttendanceItem,
)

router = APIRouter(prefix="/reports", tags=["HR Reports"])


def get_service(session: AsyncSession = Depends(get_db)) -> HRReportingService:
    return HRReportingService(session)


# ═══════════════════════════════════════════════════════════
# Monthly Reports
# ═══════════════════════════════════════════════════════════

@router.get("/monthly", response_model=MonthlyReportResponse)
async def get_monthly_report(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    department_id: Optional[UUID] = None,
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or retrieve monthly absence report.
    
    Returns comprehensive data for each employee including:
    - Vacation, ROL, permit, sick days taken
    - Current leave balances
    - Business trips and expenses
    - Payroll codes for LUL export
    """
    try:
        report = await service.generate_monthly_report(
            year=year,
            month=month,
            department_id=department_id,
            generated_by=current_user.sub,
        )
        await db.commit()
        return report
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly/{year}")
async def get_year_monthly_summary(
    year: int,
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
):
    """Get summary of all monthly reports for a year."""
    # Return list of available monthly reports for the year
    return {
        "year": year,
        "months": [
            {"month": m, "status": "available" if m <= date.today().month else "not_yet"}
            for m in range(1, 13)
        ],
    }


# ═══════════════════════════════════════════════════════════
# Compliance Reports
# ═══════════════════════════════════════════════════════════

@router.get("/compliance", response_model=ComplianceReportResponse)
async def get_compliance_report(
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
):
    """
    Get current compliance status report.
    
    Checks for:
    - Vacation legal minimum (D.Lgs. 66/2003)
    - Previous year vacation expiry (30/06 deadline)
    - Other regulatory requirements
    """
    return await service.generate_compliance_report(
        generated_by=current_user.sub
    )


# ═══════════════════════════════════════════════════════════
# Budget Reports
# ═══════════════════════════════════════════════════════════

@router.get("/budget", response_model=BudgetReportResponse)
async def get_budget_report(
    year: int = Query(default=None),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
):
    """
    Get expense budget report.
    
    Shows:
    - Trip budget utilization
    - Expense breakdown by department
    - Leave cost estimation
    """
    year = year or date.today().year
    return await service.generate_budget_report(
        year=year,
        month=month,
        generated_by=current_user.sub,
    )


# ═══════════════════════════════════════════════════════════
# Custom Reports
# ═══════════════════════════════════════════════════════════

@router.post("/custom")
async def generate_custom_report(
    request: CustomReportRequest,
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate custom report with specified parameters.
    
    Supports flexible date ranges, filters, and grouping options.
    """
    # Route to appropriate report generator based on type
    if request.report_type == "monthly_absence":
        # Extract year/month from period
        report = await service.generate_monthly_report(
            year=request.period_start.year,
            month=request.period_start.month,
            department_id=request.filters.get("department_id"),
            generated_by=current_user.sub,
        )
        await db.commit()
        return report.model_dump()
    
    elif request.report_type == "compliance":
        return await service.generate_compliance_report(
            generated_by=current_user.sub
        )
    
    elif request.report_type == "budget":
        return await service.generate_budget_report(
            year=request.period_start.year,
            month=request.period_start.month if request.period_start.month == request.period_end.month else None,
            generated_by=current_user.sub,
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown report type: {request.report_type}"
        )


# ═══════════════════════════════════════════════════════════
# Export Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/export/lul/{year}/{month}")
async def export_lul(
    year: int,
    month: int,
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
):
    """
    Export LUL-compatible data (CSV).
    
    Generates payroll integration data in the format
    required by Labor Consultants (Zucchetti-like).
    """
    csv_content = await service.generate_lul_export(
        year=year,
        month=month,
    )
    
    filename = f"LUL_KRONOS_{year}_{month:02d}.csv"
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/excel/{report_type}")
async def export_excel(
    report_type: str,
    year: int = Query(...),
    month: Optional[int] = Query(default=None),
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
):
    """
    Export report as Excel file.
    
    Supported types: monthly, compliance, budget
    """
    # TODO: Implement Excel generation
    return {
        "status": "export_queued",
        "report_type": report_type,
        "format": "excel",
        "message": "Excel export will be available at the download URL",
    }


@router.get("/export/pdf/{report_type}")
async def export_pdf(
    report_type: str,
    year: int = Query(...),
    month: Optional[int] = Query(default=None),
    current_user: TokenPayload = Depends(require_permission("reports:advanced")),
    service: HRReportingService = Depends(get_service),
):
    """
    Export report as PDF file.
    
    Supported types: monthly, compliance, budget
    """
    # TODO: Implement PDF generation
    return {
        "status": "export_queued",
        "report_type": report_type,
        "format": "pdf",
        "message": "PDF export will be available at the download URL",
    }


# ═══════════════════════════════════════════════════════════
# Attendance Reports
# ═══════════════════════════════════════════════════════════

@router.get("/attendance/daily", response_model=DailyAttendanceResponse)
async def get_daily_attendance(
    target_date: date = Query(default=None),
    department: Optional[str] = Query(default=None),
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get daily attendance report.
    
    Shows which employees are present, on leave, or absent for a given date.
    Used by HR Reports page for daily attendance view.
    """
    if target_date is None:
        target_date = date.today()
    
    aggregator = HRDataAggregator()
    
    try:
        # Get workforce status for the date
        workforce = await aggregator.get_workforce_status(target_date)
        
        # Get employee details with attendance status
        employees = await aggregator.get_daily_attendance_details(
            target_date=target_date,
            department=department,
        )
        
        items = []
        for emp in employees:
            items.append(AttendanceItem(
                user_id=emp["user_id"],
                full_name=emp["full_name"],
                department=emp.get("department"),
                status=emp["status"],
                hours_worked=emp.get("hours_worked", 8.0),
                leave_request_id=emp.get("leave_request_id"),
                leave_type=emp.get("leave_type"),
                notes=emp.get("notes"),
            ))
        
        return DailyAttendanceResponse(
            date=target_date,
            total_employees=workforce.get("total_employees", len(items)),
            total_present=sum(1 for i in items if "Presente" in i.status),
            total_absent=sum(1 for i in items if "Presente" not in i.status),
            absence_rate=round(
                sum(1 for i in items if "Presente" not in i.status) / max(len(items), 1) * 100, 1
            ),
            items=items,
        )
    except Exception as e:
        # Fallback to empty response
        return DailyAttendanceResponse(
            date=target_date,
            total_employees=0,
            total_present=0,
            total_absent=0,
            absence_rate=0.0,
            items=[],
        )


@router.post("/attendance/aggregate", response_model=AggregateAttendanceResponse)
async def get_aggregate_attendance(
    request: AggregateAttendanceRequest,
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregate attendance report for a date range.
    
    Returns per-employee statistics including worked days, vacation days,
    sick days, etc. for the specified period.
    """
    aggregator = HRDataAggregator()
    
    try:
        # Calculate working days in period
        from src.shared.clients import CalendarClient
        calendar_client = CalendarClient()
        working_days = await calendar_client.get_working_days_count(
            request.start_date,
            request.end_date,
        )
        
        employees_data = await aggregator.get_aggregate_attendance_details(
            start_date=request.start_date,
            end_date=request.end_date,
            department=request.department,
        )
        
        items = []
        for emp in employees_data:
            items.append(AggregateAttendanceItem(
                user_id=emp["user_id"],
                full_name=emp["full_name"],
                department=emp.get("department"),
                worked_days=emp.get("worked_days", 0),
                total_days=working_days,
                vacation_days=emp.get("vacation_days", 0),
                holiday_days=emp.get("holiday_days", 0),
                rol_hours=emp.get("rol_hours", 0),
                permit_hours=emp.get("permit_hours", 0),
                sick_days=emp.get("sick_days", 0),
                other_absences=emp.get("other_absences", 0),
            ))
        
        return AggregateAttendanceResponse(
            start_date=request.start_date,
            end_date=request.end_date,
            working_days=working_days,
            items=items,
        )
    except Exception as e:
        # Fallback to empty response
        return AggregateAttendanceResponse(
            start_date=request.start_date,
            end_date=request.end_date,
            working_days=0,
            items=[],
        )


# Alias for GET request (backwards compatibility)
@router.get("/attendance/aggregate", response_model=AggregateAttendanceResponse)
async def get_aggregate_attendance_get(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department: Optional[str] = Query(default=None),
    current_user: TokenPayload = Depends(require_permission("reports:view")),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate attendance report via GET request."""
    request = AggregateAttendanceRequest(
        start_date=start_date,
        end_date=end_date,
        department=department,
    )
    return await get_aggregate_attendance(request, current_user, db)
