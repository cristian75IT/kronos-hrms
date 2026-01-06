"""
KRONOS HR Reporting Service - HR Management Router.

API endpoints for HR to view and manage all employees' leaves, trips, and expenses.
"""
from datetime import date
from typing import Optional, Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_hr, TokenPayload
from src.shared.clients import LeavesClient, ExpenseClient
# audit_action removed - use get_audit_logger instead

from ..schemas import (
    DataTableRequest,
    DataTableResponse,
    HRLeaveItem,
    HRTripItem,
    HRExpenseItem,
)

router = APIRouter(prefix="/management", tags=["HR Management"])


# ═══════════════════════════════════════════════════════════
# Leaves Management
# ═══════════════════════════════════════════════════════════

@router.get("/leaves/datatable", response_model=DataTableResponse)
async def get_all_leaves_datatable(
    request: Request,
    draw: int = Query(default=1),
    start: int = Query(default=0),
    length: int = Query(default=25),
    search_value: Optional[str] = Query(default=None, alias="search[value]"),
    status_filter: Optional[str] = Query(default=None),
    leave_type_filter: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """
    Get all employees' leave requests in DataTable format.
    HR can view all leaves across all departments.
    """
    client = LeavesClient()
    
    # Extract token
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header and "Bearer " in auth_header else None

    # Build filters for leaves service
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if leave_type_filter:
        filters["leave_type"] = leave_type_filter
    if date_from:
        filters["date_from"] = date_from.isoformat()
    if date_to:
        filters["date_to"] = date_to.isoformat()
    if search_value:
        filters["search"] = search_value
    
    try:
        # Call leaves service datatable endpoint
        response = await client.get_all_leaves_datatable(
            draw=draw,
            start=start,
            length=length,
            filters=filters,
            token=token,
        )
        
        return DataTableResponse(
            draw=draw,
            recordsTotal=response.get("recordsTotal", 0),
            recordsFiltered=response.get("recordsFiltered", 0),
            data=response.get("data", []),
        )
    except Exception as e:
        # Log error for debugging
        import logging
        logging.getLogger(__name__).error(f"HR Leaves datatable error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch leaves data: {str(e)}")




@router.get("/leaves/{leave_id}")
async def get_leave_detail(
    leave_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get full details of a leave request."""
    client = LeavesClient()
    
    try:
        leave = await client.get_leave_by_id(leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="Leave request not found")
        return leave
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/leaves/{leave_id}")
async def update_leave(
    leave_id: UUID,
    data: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """
    HR can update a leave request.
    Creates audit trail and optionally notifies the employee.
    """
    client = LeavesClient()
    
    try:
        # Get original leave for audit
        original = await client.get_leave_by_id(leave_id)
        if not original:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        # Update leave
        updated = await client.update_leave_hr(leave_id, data)
        
        # TODO: Add audit logging
        # TODO: Send notification to employee about the change
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Trips Management
# ═══════════════════════════════════════════════════════════

@router.get("/trips/datatable", response_model=DataTableResponse)
async def get_all_trips_datatable(
    request: Request,
    draw: int = Query(default=1),
    start: int = Query(default=0),
    length: int = Query(default=25),
    search_value: Optional[str] = Query(default=None, alias="search[value]"),
    status_filter: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """
    Get all employees' business trips in DataTable format.
    """
    client = ExpenseClient()
    
    # Extract token
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header and "Bearer " in auth_header else None

    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if date_from:
        filters["date_from"] = date_from.isoformat()
    if date_to:
        filters["date_to"] = date_to.isoformat()
    if search_value:
        filters["search"] = search_value
    
    try:
        response = await client.get_all_trips_datatable(
            draw=draw,
            start=start,
            length=length,
            filters=filters,
            token=token,
        )
        
        return DataTableResponse(
            draw=draw,
            recordsTotal=response.get("recordsTotal", 0),
            recordsFiltered=response.get("recordsFiltered", 0),
            data=response.get("data", []),
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"HR Trips datatable error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trips data: {str(e)}")



@router.get("/trips/{trip_id}")
async def get_trip_detail(
    trip_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get full details of a business trip."""
    client = ExpenseClient()
    
    try:
        trip = await client.get_trip_by_id(trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        return trip
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/trips/{trip_id}")
async def update_trip(
    trip_id: UUID,
    data: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """HR can update a business trip."""
    client = ExpenseClient()
    
    try:
        original = await client.get_trip_by_id(trip_id)
        if not original:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        updated = await client.update_trip_hr(trip_id, data)
        
        # TODO: Add audit logging
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Expenses Management
# ═══════════════════════════════════════════════════════════

@router.get("/expenses/datatable", response_model=DataTableResponse)
async def get_all_expenses_datatable(
    request: Request,
    draw: int = Query(default=1),
    start: int = Query(default=0),
    length: int = Query(default=25),
    search_value: Optional[str] = Query(default=None, alias="search[value]"),
    status_filter: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """
    Get all employees' expense reports in DataTable format.
    """
    client = ExpenseClient()
    
    # Extract token
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header and "Bearer " in auth_header else None

    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if date_from:
        filters["date_from"] = date_from.isoformat()
    if date_to:
        filters["date_to"] = date_to.isoformat()
    if search_value:
        filters["search"] = search_value
    
    try:
        response = await client.get_all_expenses_datatable(
            draw=draw,
            start=start,
            length=length,
            filters=filters,
            token=token,
        )
        
        return DataTableResponse(
            draw=draw,
            recordsTotal=response.get("recordsTotal", 0),
            recordsFiltered=response.get("recordsFiltered", 0),
            data=response.get("data", []),
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"HR Expenses datatable error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch expenses data: {str(e)}")



@router.get("/expenses/{expense_id}")
async def get_expense_detail(
    expense_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Get full details of an expense report."""
    client = ExpenseClient()
    
    try:
        expense = await client.get_expense_by_id(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense report not found")
        return expense
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/expenses/{expense_id}")
async def update_expense(
    expense_id: UUID,
    data: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """HR can update an expense report."""
    client = ExpenseClient()
    
    try:
        original = await client.get_expense_by_id(expense_id)
        if not original:
            raise HTTPException(status_code=404, detail="Expense report not found")
        
        updated = await client.update_expense_hr(expense_id, data)
        
        # TODO: Add audit logging
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
