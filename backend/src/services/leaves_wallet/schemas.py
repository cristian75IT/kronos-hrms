from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WalletTransactionResponse(BaseModel):
    id: UUID
    reference_id: Optional[UUID] = None
    transaction_type: str
    balance_type: str
    amount: Decimal
    remaining_amount: Decimal
    balance_after: Decimal
    expiry_date: Optional[date] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    year: int
    
    # Vacation
    vacation_previous_year: Decimal
    vacation_current_year: Decimal
    vacation_accrued: Decimal
    vacation_used: Decimal
    vacation_used_ap: Decimal
    vacation_used_ac: Decimal
    vacation_available_total: Decimal
    
    # ROL
    rol_previous_year: Decimal
    rol_current_year: Decimal
    rol_accrued: Decimal
    rol_used: Decimal
    rol_available: Decimal
    
    # Permits
    permits_total: Decimal
    permits_used: Decimal
    permits_available: Decimal
    
    last_accrual_date: Optional[date] = None
    
    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    user_id: UUID
    reference_id: Optional[UUID] = None
    transaction_type: str  # 'deduction', 'accrual', 'refund', 'adjustment', 'carry_over'
    balance_type: str      # 'vacation', 'vacation_ap', 'vacation_ac', 'rol', 'permits'
    amount: Decimal
    expiry_date: Optional[date] = None
    description: Optional[str] = None
    created_by: Optional[UUID] = None


class AccrualRequest(BaseModel):
    # For manual trigger of monthly accrual
    year: int
    month: int
    user_ids: Optional[List[UUID]] = None  # None = All active users
