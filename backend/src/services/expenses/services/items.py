"""
KRONOS - Expense Service - Items Module

Handles Individual Expense Items within Reports.
"""
import logging
from uuid import UUID

from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.expenses.models import ExpenseReportStatus
from src.services.expenses.schemas import (
    ExpenseItemCreate,
    ExpenseItemUpdate,
)
from src.services.expenses.services.base import BaseExpenseService

logger = logging.getLogger(__name__)


class ExpenseItemService(BaseExpenseService):
    """
    Sub-service for Expense Items management.
    """

    async def add_item(self, user_id: UUID, data: ExpenseItemCreate):
        """Add expense item to report."""
        report = await self._report_repo.get(data.report_id)
        if not report:
             raise NotFoundError("Expense report not found")
        
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot add items to another user's report")
            
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Can only add items to draft reports")
            
        # Get category from config
        expense_type = await self._get_expense_type(data.expense_type_id)
        category = "OTHER"
        if expense_type:
            category = self._map_expense_category(expense_type.get("code", ""))
            
        item = await self._item_repo.create(
            category=category,
            **data.model_dump(),
        )
        
        # Update report total
        await self._report_repo.recalculate_total(data.report_id)
        
        return item

    async def update_item(self, id: UUID, user_id: UUID, data: ExpenseItemUpdate):
        """Update expense item."""
        item = await self._item_repo.get(id)
        if not item:
            raise NotFoundError("Expense item not found")
            
        report = await self._report_repo.get(item.report_id)
        if not report:
             raise NotFoundError("Parent report not found")
            
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot update items in another user's report")
            
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Can only update items in draft reports")
            
        # If type changed, update category
        update_data = data.model_dump(exclude_unset=True)
        if "expense_type_id" in update_data:
            expense_type = await self._get_expense_type(data.expense_type_id)
            if expense_type:
                update_data["category"] = self._map_expense_category(expense_type.get("code", ""))
                
        updated_item = await self._item_repo.update(id, **update_data)
        
        # Update report total
        await self._report_repo.recalculate_total(report.id)
        
        return updated_item

    async def delete_item(self, id: UUID, user_id: UUID):
        """Delete expense item."""
        item = await self._item_repo.get(id)
        if not item:
            raise NotFoundError("Expense item not found")
            
        report = await self._report_repo.get(item.report_id)
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot delete items from another user's report")
            
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Can only delete items from draft reports")
            
        await self._item_repo.delete(id)
        
        # Update report total
        await self._report_repo.recalculate_total(report.id)
        
        return True
