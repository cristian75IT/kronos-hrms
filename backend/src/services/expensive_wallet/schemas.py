from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Schema for creating a wallet transaction."""
    transaction_type: str = Field(..., description="Type of transaction (budget_allocation, advance_payment, expense_approval, reimbursement_payment)")
    amount: Decimal
    reference_id: Optional[UUID] = None
    description: Optional[str] = None
    created_by: Optional[UUID] = None


class TripWalletTransactionResponse(BaseModel):
    """Schema for wallet transaction response."""
    id: UUID
    transaction_type: str
    amount: Decimal
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
    current_balance: Decimal
    net_to_pay: Decimal
    created_at: datetime
    updated_at: datetime
    
    transactions: List[TripWalletTransactionResponse] = []

    class Config:
        from_attributes = True


class WalletSummary(BaseModel):
    """Summary of the wallet for the trip."""
    total_budget: Decimal
    total_advances: Decimal
    total_expenses: Decimal
    remaining_budget: Decimal
    reimbursement_due: Decimal
