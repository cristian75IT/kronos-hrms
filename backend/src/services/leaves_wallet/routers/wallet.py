from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_admin
from ..service import WalletService
from ..models import EmployeeWallet
from ..schemas import WalletResponse, TransactionCreate, WalletTransactionResponse

router = APIRouter()

@router.get("/{user_id}", response_model=WalletResponse)
async def get_user_wallet(
    user_id: UUID, 
    year: int = None,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # Authorization check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this wallet")
        
    if not year:
        year = datetime.now().year
        
    service = WalletService(session)
    wallet = await service.get_wallet(user_id, year)
    return wallet

@router.post("/{user_id}/transactions", response_model=WalletTransactionResponse)
async def create_transaction(
    user_id: UUID,
    transaction: TransactionCreate,
    current_user = Depends(require_admin), # Only admins or system (via admin token) can adjust
    session: AsyncSession = Depends(get_db)
):
    if transaction.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    
    transaction.created_by = current_user.id
    service = WalletService(session)
    return await service.process_transaction(transaction)

@router.get("/{user_id}/transactions", response_model=list[WalletTransactionResponse])
async def get_user_transactions(
    user_id: UUID,
    year: int = None,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # Authorization check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view these transactions")
        
    service = WalletService(session)
    wallet = await service.get_wallet(user_id, year or datetime.now().year)
    return await service.get_transactions(wallet.id)
@router.get("/transactions/{wallet_id}", response_model=list[WalletTransactionResponse])
async def get_wallet_transactions(
    wallet_id: UUID,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    service = WalletService(session)
    # Authorization might be tricky here without knowing the user_id. 
    # For now, admin only or we'd need to fetch the wallet first.
    if not current_user.is_admin:
         # Check if wallet belongs to user
         stmt = select(EmployeeWallet.user_id).where(EmployeeWallet.id == wallet_id)
         res = await session.execute(stmt)
         owner_id = res.scalar_one_or_none()
         if owner_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized")
             
    return await service.get_transactions(wallet_id)
