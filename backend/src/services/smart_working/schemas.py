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

WEEKDAY_NAMES = {
    0: "Lunedì",
    1: "Martedì", 
    2: "Mercoledì",
    3: "Giovedì",
    4: "Venerdì"
}

class SWAgreementCreate(BaseModel):
    user_id: UUID
    start_date: date
    end_date: Optional[date] = None
    allowed_days_per_week: int = Field(default=2, ge=1, le=5)
    allowed_weekdays: Optional[List[int]] = Field(
        None,
        description="Weekdays allowed: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday"
    )
    notes: Optional[str] = None
    metadata_fields: Optional[Dict[str, Any]] = None

    @field_validator('allowed_weekdays')
    @classmethod
    def validate_weekdays(cls, v: Optional[List[int]], info) -> Optional[List[int]]:
        if v is None:
            return v
        
        # Check valid weekday range (0-4, Mon-Fri)
        if any(d < 0 or d > 4 for d in v):
            raise ValueError('I giorni devono essere tra 0 (Lunedì) e 4 (Venerdì)')
        
        # Check no duplicates
        if len(v) != len(set(v)):
            raise ValueError('Giorni duplicati non sono permessi')
        
        # Check count matches allowed_days_per_week
        days_per_week = info.data.get('allowed_days_per_week', 2)
        if len(v) != days_per_week:
            raise ValueError(f'Devi selezionare esattamente {days_per_week} giorni')
        
        return sorted(v)

class SWAgreementUpdate(BaseModel):
    end_date: Optional[date] = None
    allowed_days_per_week: Optional[int] = Field(None, ge=1, le=5)
    allowed_weekdays: Optional[List[int]] = Field(None)
    status: Optional[SWAgreementStatus] = None
    notes: Optional[str] = None
    metadata_fields: Optional[Dict[str, Any]] = None

class SWAgreementResponse(BaseModel):
    id: UUID
    user_id: UUID
    start_date: date
    end_date: Optional[date]
    allowed_days_per_week: int
    allowed_weekdays: Optional[List[int]]
    allowed_weekdays_names: Optional[List[str]] = None  # Computed for UI
    status: SWAgreementStatus
    notes: Optional[str]
    metadata_fields: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True

    def model_post_init(self, __context: Any) -> None:
        if self.allowed_weekdays:
            self.allowed_weekdays_names = [WEEKDAY_NAMES.get(d, str(d)) for d in self.allowed_weekdays]

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

class SWPresenceCreate(BaseModel):
    date: date
    notes: Optional[str] = "Lavoro in presenza"

class SWSignRequest(BaseModel):
    otp_code: str = Field(..., min_length=6, max_length=6, description="Codice OTP 6 cifre")

