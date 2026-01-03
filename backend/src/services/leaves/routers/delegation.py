"""
KRONOS Leave Service - Delegation Router

Endpoints for managing approval delegations.
Allows managers to delegate their approval authority during absence.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.core.database import get_db
from src.core.security import get_current_user, require_approver as require_manager, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.leaves.models import ApprovalDelegation
from src.services.leaves.schemas import (
    CreateDelegationRequest,
    DelegationResponse,
)

router = APIRouter(prefix="/delegations", tags=["Approval Delegations"])


# ═══════════════════════════════════════════════════════════════════
# Delegation Management
# ═══════════════════════════════════════════════════════════════════

@router.get("/", response_model=list[DelegationResponse])
async def get_my_delegations(
    include_inactive: bool = Query(default=False),
    token: TokenPayload = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all delegations I have created.
    
    Shows who I have delegated my approval authority to.
    """
    stmt = select(ApprovalDelegation).where(
        ApprovalDelegation.delegator_id == token.sub
    )
    
    if not include_inactive:
        stmt = stmt.where(ApprovalDelegation.is_active == True)
    
    result = await db.execute(stmt.order_by(ApprovalDelegation.created_at.desc()))
    delegations = result.scalars().all()
    
    return [DelegationResponse.model_validate(d, from_attributes=True) for d in delegations]


@router.get("/received", response_model=list[DelegationResponse])
async def get_received_delegations(
    active_only: bool = Query(default=True),
    token: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all delegations I have received.
    
    Shows whose approval authority has been delegated to me.
    """
    today = date.today()
    
    stmt = select(ApprovalDelegation).where(
        ApprovalDelegation.delegate_id == token.sub
    )
    
    if active_only:
        stmt = stmt.where(
            ApprovalDelegation.is_active == True,
            ApprovalDelegation.start_date <= today,
            ApprovalDelegation.end_date >= today,
        )
    
    result = await db.execute(stmt.order_by(ApprovalDelegation.created_at.desc()))
    delegations = result.scalars().all()
    
    return [DelegationResponse.model_validate(d, from_attributes=True) for d in delegations]


@router.post("/", response_model=DelegationResponse, status_code=201)
async def create_delegation(
    data: CreateDelegationRequest,
    token: TokenPayload = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new approval delegation.
    
    Delegate your approval authority to another manager for a specific period.
    Commonly used when going on vacation.
    """
    # Cannot delegate to self
    if data.delegate_id == token.sub:
        raise HTTPException(status_code=400, detail="Cannot delegate to yourself")
    
    # Check for overlapping active delegations
    overlap_stmt = select(ApprovalDelegation).where(
        and_(
            ApprovalDelegation.delegator_id == token.sub,
            ApprovalDelegation.delegate_id == data.delegate_id,
            ApprovalDelegation.is_active == True,
            ApprovalDelegation.start_date <= data.end_date,
            ApprovalDelegation.end_date >= data.start_date,
        )
    )
    result = await db.execute(overlap_stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Overlapping delegation exists for this delegate ({existing.start_date} - {existing.end_date})"
        )
    
    # Create delegation
    delegation = ApprovalDelegation(
        delegator_id=token.sub,
        delegate_id=data.delegate_id,
        start_date=data.start_date,
        end_date=data.end_date,
        delegation_type=data.delegation_type.value,
        scope_leave_types=data.scope_leave_types,
        reason=data.reason,
        is_active=True,
    )
    
    db.add(delegation)
    await db.flush()
    
    return DelegationResponse.model_validate(delegation, from_attributes=True)


@router.get("/{delegation_id}", response_model=DelegationResponse)
async def get_delegation(
    delegation_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific delegation."""
    result = await db.execute(
        select(ApprovalDelegation).where(ApprovalDelegation.id == delegation_id)
    )
    delegation = result.scalar_one_or_none()
    
    if not delegation:
        raise HTTPException(status_code=404, detail="Delegation not found")
    
    # Only delegator or delegate can view
    if delegation.delegator_id != token.sub and delegation.delegate_id != token.sub:
        raise HTTPException(status_code=403, detail="Not authorized to view this delegation")
    
    return DelegationResponse.model_validate(delegation, from_attributes=True)


@router.post("/{delegation_id}/revoke")
async def revoke_delegation(
    delegation_id: UUID,
    reason: Optional[str] = None,
    token: TokenPayload = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke an active delegation.
    
    Only the delegator can revoke their own delegations.
    """
    result = await db.execute(
        select(ApprovalDelegation).where(ApprovalDelegation.id == delegation_id)
    )
    delegation = result.scalar_one_or_none()
    
    if not delegation:
        raise HTTPException(status_code=404, detail="Delegation not found")
    
    if delegation.delegator_id != token.sub:
        raise HTTPException(status_code=403, detail="Only the delegator can revoke")
    
    if not delegation.is_active:
        raise HTTPException(status_code=400, detail="Delegation already inactive")
    
    delegation.is_active = False
    delegation.revoked_at = datetime.utcnow()
    delegation.revoked_by = token.sub
    
    await db.flush()
    
    return {"message": "Delegation revoked", "id": str(delegation_id)}


@router.delete("/{delegation_id}", status_code=204)
async def delete_delegation(
    delegation_id: UUID,
    token: TokenPayload = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a delegation (only if not yet started).
    
    Use revoke instead if delegation is active or has been used.
    """
    result = await db.execute(
        select(ApprovalDelegation).where(ApprovalDelegation.id == delegation_id)
    )
    delegation = result.scalar_one_or_none()
    
    if not delegation:
        raise HTTPException(status_code=404, detail="Delegation not found")
    
    if delegation.delegator_id != token.sub:
        raise HTTPException(status_code=403, detail="Only the delegator can delete")
    
    # Only allow deletion if not yet started
    if delegation.start_date <= date.today():
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete a delegation that has started. Use revoke instead."
        )
    
    await db.delete(delegation)
    await db.flush()


# ═══════════════════════════════════════════════════════════════════
# Delegation Checking Utilities
# ═══════════════════════════════════════════════════════════════════

async def get_active_delegations_for_user(
    delegate_id: UUID,
    db: AsyncSession,
    leave_type_code: Optional[str] = None,
) -> list[ApprovalDelegation]:
    """
    Get all currently active delegations for a user (the delegate).
    
    Used internally to check if a user can approve on behalf of others.
    """
    today = date.today()
    
    stmt = select(ApprovalDelegation).where(
        and_(
            ApprovalDelegation.delegate_id == delegate_id,
            ApprovalDelegation.is_active == True,
            ApprovalDelegation.start_date <= today,
            ApprovalDelegation.end_date >= today,
            ApprovalDelegation.delegation_type == "FULL",  # Only full delegations can approve
        )
    )
    
    result = await db.execute(stmt)
    delegations = result.scalars().all()
    
    # Filter by leave type if specified
    if leave_type_code:
        delegations = [
            d for d in delegations 
            if not d.scope_leave_types or leave_type_code in d.scope_leave_types
        ]
    
    return delegations


async def can_approve_for_delegator(
    delegate_id: UUID,
    delegator_id: UUID,
    db: AsyncSession,
    leave_type_code: Optional[str] = None,
) -> bool:
    """
    Check if delegate_id can approve on behalf of delegator_id.
    
    Returns True if there's an active FULL delegation from delegator to delegate.
    """
    delegations = await get_active_delegations_for_user(delegate_id, db, leave_type_code)
    return any(d.delegator_id == delegator_id for d in delegations)
