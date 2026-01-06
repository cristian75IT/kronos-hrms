from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Schema for creating a wallet transaction."""
    transaction_type: str = Field(..., description="Type of transaction (budget_allocation, advance_payment, expense_approval, reimbursement_payment)")
    amount: Decimal
    category: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    is_reimbursable: bool = True
    is_taxable: bool = False
    has_receipt: bool = True
    reference_id: Optional[UUID] = None
    description: Optional[str] = None
    created_by: Optional[UUID] = None


class TripWalletTransactionResponse(BaseModel):
    """Schema for wallet transaction response."""
    id: UUID
    transaction_type: str
    amount: Decimal
    category: Optional[str] = None
    tax_amount: Optional[Decimal] = None
    is_reimbursable: bool
    is_taxable: bool
    has_receipt: bool
    compliance_flags: Optional[str] = None
    reference_id: Optional[UUID]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TripWalletResponse(BaseModel):
    """Schema for trip wallet response."""
    id: UUID
    trip_id: UUID
    user_id: UUID
    total_budget: Decimal
    total_advances: Decimal
    total_expenses: Decimal
    total_taxable: Decimal
    total_non_taxable: Decimal
    currency: str
    status: str
    policy_violations_count: int
    is_reconciled: bool
    current_balance: Decimal
    net_to_pay: Decimal
    created_at: datetime
    updated_at: datetime
    
    transactions: List[TripWalletTransactionResponse] = []

    class Config:
        from_attributes = True


class WalletBudgetSummary(BaseModel):
    total: float
    reserved: float
    available: float


class WalletExpenseSummary(BaseModel):
    total: float
    taxable: float
    non_taxable: float


class WalletAdvanceSummary(BaseModel):
    total: float


class WalletSettlementSummary(BaseModel):
    current_balance: float
    net_to_pay: float


class WalletComplianceSummary(BaseModel):
    policy_violations_count: int
    is_reconciled: bool


class WalletTimestampSummary(BaseModel):
    created_at: str
    updated_at: str


class WalletSummary(BaseModel):
    """Comprehensive wallet summary."""
    wallet_id: str
    trip_id: str
    user_id: str
    currency: str
    status: str
    budget: WalletBudgetSummary
    expenses: WalletExpenseSummary
    advances: WalletAdvanceSummary
    settlement: WalletSettlementSummary
    compliance: WalletComplianceSummary
    timestamps: WalletTimestampSummary


# ═══════════════════════════════════════════════════════════
# Request Schemas
# ═══════════════════════════════════════════════════════════

class BudgetReserveRequest(BaseModel):
    amount: Decimal
    reference_id: UUID
    category: Optional[str] = None
    description: Optional[str] = None


class PolicyCheckRequest(BaseModel):
    category: str
    amount: Decimal


class ProcessTransactionRequest(BaseModel):
    transaction_type: str
    amount: Decimal
    reference_id: Optional[UUID] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    is_taxable: bool = False
    has_receipt: bool = True
    is_reimbursable: bool = True


class ReconciliationRequest(BaseModel):
    notes: Optional[str] = None
    adjustments: Optional[List[Dict[str, Any]]] = None


class SettlementRequest(BaseModel):
    payment_reference: Optional[str] = None


class UpdateBudgetRequest(BaseModel):
    new_budget: Decimal
    reason: str


class VoidTransactionRequest(BaseModel):
    reason: str
