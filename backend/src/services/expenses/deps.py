from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.expenses.services import ExpenseService

async def get_expense_service(
    session: AsyncSession = Depends(get_db),
) -> ExpenseService:
    """Dependency for ExpenseService."""
    return ExpenseService(session)
