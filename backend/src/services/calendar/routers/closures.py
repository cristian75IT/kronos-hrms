"""KRONOS Calendar Service - Closures Router."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_hr, TokenPayload
from ..schemas import ClosureCreate, ClosureUpdate, ClosureResponse
from ..service import CalendarService

router = APIRouter()


@router.get("", response_model=List[ClosureResponse])
async def list_closures(
    year: Optional[int] = Query(None, description="Filter by year"),
    include_inactive: bool = Query(False, description="Include inactive closures"),
    db: AsyncSession = Depends(get_db),
    # No auth required for read - allows service-to-service calls
):
    """Get all company closures with optional filters."""
    service = CalendarService(db)
    closures = await service.get_closures(
        year=year,
        include_inactive=include_inactive,
    )
    return closures


@router.get("/{closure_id}", response_model=ClosureResponse)
async def get_closure(
    closure_id: UUID,
    db: AsyncSession = Depends(get_db),
    # No auth required for read - allows service-to-service calls
):
    """Get a specific closure by ID."""
    service = CalendarService(db)
    closure = await service.get_closure(closure_id)
    if not closure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Closure not found",
        )
    return closure


@router.post("", response_model=ClosureResponse, status_code=status.HTTP_201_CREATED)
async def create_closure(
    data: ClosureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Create a new company closure. Requires HR or Admin privileges."""
    service = CalendarService(db)
    closure = await service.create_closure(
        data=data,
        created_by=current_user.user_id,
    )
    return closure


@router.put("/{closure_id}", response_model=ClosureResponse)
async def update_closure(
    closure_id: UUID,
    data: ClosureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Update an existing closure. Requires HR or Admin privileges."""
    service = CalendarService(db)
    closure = await service.update_closure(closure_id, data, user_id=current_user.user_id)
    if not closure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Closure not found",
        )
    return closure


@router.delete("/{closure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_closure(
    closure_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Delete a closure. Requires HR or Admin privileges."""
    service = CalendarService(db)
    success = await service.delete_closure(closure_id, user_id=current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Closure not found",
        )
    return None
