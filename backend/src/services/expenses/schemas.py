"""KRONOS Expense Service - Pydantic Schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.shared.schemas import BaseSchema, IDMixin, DataTableResponse, DataTableRequest
from src.services.expenses.models import TripStatus, ExpenseReportStatus, DestinationType


# ═══════════════════════════════════════════════════════════
# Business Trip Schemas
# ═══════════════════════════════════════════════════════════

class AttachmentResponse(IDMixin, BaseSchema):
    """Response schema for file attachment."""
    
    filename: str
    file_path: str
    content_type: str
    size_bytes: int
    created_at: datetime


class BusinessTripBase(BaseModel):
    """Base business trip schema."""
    
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    destination: str = Field(..., max_length=200)
    destination_type: DestinationType = DestinationType.NATIONAL
    start_date: date
    end_date: date
    purpose: Optional[str] = None
    project_code: Optional[str] = Field(None, max_length=50)
    client_name: Optional[str] = Field(None, max_length=200)
    estimated_budget: Optional[Decimal] = Field(None, ge=0)


class BusinessTripCreate(BusinessTripBase):
    """Schema for creating business trip."""
    pass


class BusinessTripUpdate(BaseModel):
    """Schema for updating business trip."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    destination_type: Optional[DestinationType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    purpose: Optional[str] = None
    project_code: Optional[str] = None
    client_name: Optional[str] = None
    estimated_budget: Optional[Decimal] = None


class BusinessTripResponse(BusinessTripBase, IDMixin, BaseSchema):
    """Response schema for business trip."""
    
    user_id: UUID
    status: TripStatus
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    approver_notes: Optional[str] = None
    attachment_path: Optional[str] = None  # Deprecated in favor of attachments list
    attachments: list[AttachmentResponse] = []
    total_days: int
    created_at: datetime
    updated_at: datetime


class BusinessTripListItem(BaseModel):
    """Simplified trip for lists."""
    
    id: UUID
    user_id: UUID
    title: str
    destination: str
    start_date: date
    end_date: date
    status: TripStatus
    estimated_budget: Optional[Decimal] = None
    
    model_config = {"from_attributes": True}


class TripDataTableRequest(DataTableRequest):
    """DataTable request including filters."""
    status: Optional[str] = None


class TripAdminDataTableItem(BusinessTripListItem):
    """Trip item for admin datatable with user name."""
    user_name: Optional[str] = None
    days_count: int = 0
    total_allowance: Decimal = Decimal(0)
    created_at: datetime


class TripDataTableResponse(DataTableResponse[BusinessTripListItem]):
    """DataTable response for trips (user view)."""
    pass


class TripAdminDataTableResponse(DataTableResponse[TripAdminDataTableItem]):
    """DataTable response for trips (admin view)."""
    pass


# ═══════════════════════════════════════════════════════════
# Daily Allowance Schemas
# ═══════════════════════════════════════════════════════════

class DailyAllowanceBase(BaseModel):
    """Base daily allowance schema."""
    
    date: date
    is_full_day: bool = True
    breakfast_provided: bool = False
    lunch_provided: bool = False
    dinner_provided: bool = False
    notes: Optional[str] = None


class DailyAllowanceCreate(DailyAllowanceBase):
    """Schema for creating daily allowance."""
    pass


class DailyAllowanceResponse(DailyAllowanceBase, IDMixin, BaseSchema):
    """Response schema for daily allowance."""
    
    trip_id: UUID
    base_amount: Decimal
    meals_deduction: Decimal
    final_amount: Decimal


class GenerateAllowancesRequest(BaseModel):
    """Request to auto-generate allowances for a trip."""
    
    trip_id: UUID


# ═══════════════════════════════════════════════════════════
# Expense Report Schemas
# ═══════════════════════════════════════════════════════════

class ExpenseReportBase(BaseModel):
    """Base expense report schema."""
    
    title: str = Field(..., max_length=200)
    period_start: date
    period_end: date
    employee_notes: Optional[str] = None


class ExpenseReportCreate(ExpenseReportBase):
    """Schema for creating expense report."""
    
    trip_id: UUID


class ExpenseReportResponse(ExpenseReportBase, IDMixin, BaseSchema):
    """Response schema for expense report."""
    
    trip_id: UUID
    user_id: UUID
    report_number: str
    total_amount: Decimal
    approved_amount: Optional[Decimal] = None
    status: ExpenseReportStatus
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    approver_notes: Optional[str] = None
    attachment_path: Optional[str] = None  # Deprecated in favor of attachments list
    attachments: list[AttachmentResponse] = []
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExpenseReportWithItems(ExpenseReportResponse):
    """Report with expense items."""
    
    items: list["ExpenseItemResponse"] = []


class ExpenseReportListItem(BaseModel):
    """Simplified report for lists."""
    
    id: UUID
    report_number: str
    title: str
    total_amount: Decimal
    status: ExpenseReportStatus
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ExpenseAdminDataTableItem(BaseSchema):
    """Expense report item for admin datatable."""
    
    id: UUID
    report_number: str
    title: str
    employee_id: UUID
    employee_name: str
    department: Optional[str] = None
    trip_id: Optional[UUID] = None
    trip_title: Optional[str] = None
    trip_destination: Optional[str] = None
    trip_start_date: Optional[date] = None
    trip_end_date: Optional[date] = None
    total_amount: Decimal
    items_count: int = 0
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime


class ExpenseAdminDataTableResponse(DataTableResponse[ExpenseAdminDataTableItem]):
    """DataTable response for expense reports (admin view)."""
    pass


# ═══════════════════════════════════════════════════════════
# Expense Item Schemas
# ═══════════════════════════════════════════════════════════

class ExpenseItemBase(BaseModel):
    """Base expense item schema."""
    
    expense_type_id: UUID
    date: date
    description: str = Field(..., max_length=500)
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="EUR", max_length=3)
    exchange_rate: Decimal = Field(default=1, ge=0)
    km_distance: Optional[int] = Field(None, ge=0)
    merchant_name: Optional[str] = Field(None, max_length=200)
    receipt_number: Optional[str] = Field(None, max_length=100)


class ExpenseItemCreate(ExpenseItemBase):
    """Schema for creating expense item."""
    
    report_id: UUID


class ExpenseItemUpdate(BaseModel):
    """Schema for updating expense item."""
    
    date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    km_distance: Optional[int] = None
    merchant_name: Optional[str] = None
    receipt_number: Optional[str] = None


class ExpenseItemResponse(ExpenseItemBase, IDMixin, BaseSchema):
    """Response schema for expense item."""
    
    report_id: UUID
    expense_type_code: str
    amount_eur: Decimal
    km_rate: Optional[Decimal] = None
    receipt_path: Optional[str] = None
    is_approved: Optional[bool] = None
    rejection_reason: Optional[str] = None
    created_at: datetime


# ═══════════════════════════════════════════════════════════
# Workflow Actions
# ═══════════════════════════════════════════════════════════

class SubmitTripRequest(BaseModel):
    """Submit trip for approval."""
    pass


class ApproveTripRequest(BaseModel):
    """Approve trip."""
    
    notes: Optional[str] = None


class RejectTripRequest(BaseModel):
    """Reject trip."""
    
    reason: str = Field(..., min_length=10)


class SubmitReportRequest(BaseModel):
    """Submit expense report."""
    pass


class ApproveReportRequest(BaseModel):
    """Approve expense report."""
    
    approved_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    item_approvals: Optional[dict[str, bool]] = None  # {item_id: approved}


class RejectReportRequest(BaseModel):
    """Reject expense report."""
    
    reason: str = Field(..., min_length=10)


class MarkPaidRequest(BaseModel):
    """Mark report as paid."""
    
    payment_reference: str = Field(..., max_length=100)


# Forward reference resolution
ExpenseReportWithItems.model_rebuild()
