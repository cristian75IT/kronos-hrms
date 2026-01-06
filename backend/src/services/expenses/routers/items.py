from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.core.security import get_current_user, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.shared.schemas import MessageResponse
from src.services.expenses.services import ExpenseService
from src.services.expenses.deps import get_expense_service
from src.services.expenses.schemas import (
    ExpenseItemResponse,
    ExpenseItemCreate,
    ExpenseItemUpdate
)

router = APIRouter()

@router.post("/expenses/items", response_model=ExpenseItemResponse, status_code=201)
async def add_item(
    data: ExpenseItemCreate,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Add expense item."""
    user_id = token.user_id
    
    return await service.add_item(user_id, data)


@router.put("/expenses/items/{id}", response_model=ExpenseItemResponse)
async def update_item(
    id: UUID,
    data: ExpenseItemUpdate,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Update expense item."""
    user_id = token.user_id
    
    return await service.update_item(id, user_id, data)


@router.delete("/expenses/items/{id}", response_model=MessageResponse)
async def delete_item(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Delete expense item."""
    user_id = token.user_id
    
    await service.delete_item(id, user_id)
    return MessageResponse(message="Item deleted")
