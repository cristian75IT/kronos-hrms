"""
KRONOS - Smart Working Schemas
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.services.smart_working.models import SWAgreementStatus, SWRequestStatus

# -----------------------------------------------------------------------
# Shared Enums
# -----------------------------------------------------------------------
# Use the enums from models to ensure consistency or re-define if needed for API documentation

# -----------------------------------------------------------------------
# Agreements
# -----------------------------------------------------------------------

class SWAgreementCreate(BaseModel):
    user_id: UUID
    start_date: date
    end_date: Optional[date] = None
    allowed_days_per_week: int = Field(default=2, ge=1, le=5)
    notes: Optional[str] = None
    metadata_fields: Optional[Dict[str, Any]] = None

class SWAgreementUpdate(BaseModel):
    end_date: Optional[date] = None
    allowed_days_per_week: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[SWAgreementStatus] = None
    notes: Optional[str] = None
    metadata_fields: Optional[Dict[str, Any]] = None

class SWAgreementResponse(BaseModel):
    id: UUID
    user_id: UUID
    start_date: date
    end_date: Optional[date]
    allowed_days_per_week: int
    status: SWAgreementStatus
    notes: Optional[str]
    metadata_fields: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True

# -----------------------------------------------------------------------
# Requests
# -----------------------------------------------------------------------

class SWRequestCreate(BaseModel):
    agreement_id: UUID
    date: date
    notes: Optional[str] = None

class SWRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    agreement_id: UUID
    date: date
    status: SWRequestStatus
    notes: Optional[str]
    approval_request_id: Optional[UUID]
    approver_id: Optional[UUID]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    attendance: Optional['SWAttendanceResponse'] = None

    class Config:
        from_attributes = True

class ApprovalCallback(BaseModel):
    approval_request_id: UUID
    entity_type: str
    entity_id: UUID
    status: str
    final_decision_by: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

# -----------------------------------------------------------------------
# Attendance
# -----------------------------------------------------------------------

class SWAttendanceCheckIn(BaseModel):
    request_id: UUID
    location: Optional[str] = "Home"

class SWAttendanceCheckOut(BaseModel):
    request_id: UUID

class SWAttendanceResponse(BaseModel):
    id: UUID
    request_id: UUID
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
