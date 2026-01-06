"""
KRONOS - Wallet Schemas (Integrated into Leaves).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
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
    category: Optional[str] = None
    monetary_value: Optional[Decimal] = None
    description: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
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
    vacation_available_ap: Decimal
    vacation_available_ac: Decimal
    
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
    
    # HR Compliance
    legal_minimum_required: Decimal
    legal_minimum_taken: Decimal
    status: str
    hourly_rate_snapshot: Optional[Decimal] = None
    ap_expiry_date: Optional[date] = None
    
    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    user_id: UUID
    year: Optional[int] = None
    reference_id: Optional[UUID] = None
    transaction_type: str
    balance_type: str
    amount: Decimal
    expires_at: Optional[date] = None
    description: Optional[str] = None
    category: Optional[str] = None
    monetary_value: Optional[Decimal] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_by: Optional[UUID] = None


class AccrualRequest(BaseModel):
    year: int
    month: int
    user_ids: Optional[List[UUID]] = None


class BalanceSummaryResponse(BaseModel):
    year: int
    wallet_id: str
    balances: Dict[str, float]
    reserved: Dict[str, float]
