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
from src.core.security import require_admin, TokenPayload

from ..service import HRReportingService
from ..schemas import (
    MonthlyReportResponse,
    ComplianceReportResponse,
    BudgetReportResponse,
    ReportRequest,
    CustomReportRequest,
    ExportResponse,
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
    current_user: TokenPayload = Depends(require_admin),
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
    current_user: TokenPayload = Depends(require_admin),
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
    current_user: TokenPayload = Depends(require_admin),
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
    current_user: TokenPayload = Depends(require_admin),
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
    current_user: TokenPayload = Depends(require_admin),
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
    current_user: TokenPayload = Depends(require_admin),
    service: HRReportingService = Depends(get_service),
):
    """
    Export LUL-compatible data.
    
    Generates payroll integration data in the format
    required by Italian payroll systems.
    """
    report = await service.generate_monthly_report(
        year=year,
        month=month,
        generated_by=current_user.sub,
    )
    
    # Transform to LUL format
    lul_data = []
    for emp in report.employees:
        lul_data.append({
            "fiscal_code": emp.fiscal_code,
            "employee_name": emp.full_name,
            "period": f"{year}{month:02d}",
            "codes": emp.payroll_codes.model_dump(),
        })
    
    return {
        "period": f"{year}-{month:02d}",
        "format": "LUL",
        "employee_count": len(lul_data),
        "data": lul_data,
    }


@router.get("/export/excel/{report_type}")
async def export_excel(
    report_type: str,
    year: int = Query(...),
    month: Optional[int] = Query(default=None),
    current_user: TokenPayload = Depends(require_admin),
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
    current_user: TokenPayload = Depends(require_admin),
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
