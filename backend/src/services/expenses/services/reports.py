"""
KRONOS - Expense Service - Reports Module

Handles Expense Report lifecycle (Draft -> Submitted -> Approved -> Paid).
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.services.expenses.models import ExpenseReportStatus, ReportAttachment
from src.services.expenses.schemas import (
    ExpenseReportCreate,
    ApproveReportRequest,
    RejectReportRequest,
    MarkPaidRequest,
    ExpenseAdminDataTableItem,
)
from src.shared.schemas import DataTableRequest
from src.shared.storage import storage_manager
from src.services.expenses.services.base import BaseExpenseService

logger = logging.getLogger(__name__)


class ExpenseReportService(BaseExpenseService):
    """
    Sub-service for Expense Report management.
    """

    async def get_report(self, id: UUID):
        """Get expense report by ID."""
        report = await self._report_repo.get(id)
        if not report:
            raise NotFoundError("Expense report not found", entity_type="ExpenseReport", entity_id=str(id))
        return report

    async def get_user_reports(
        self,
        user_id: UUID,
        status: Optional[list[ExpenseReportStatus]] = None,
    ):
        """Get reports for a user."""
        return await self._report_repo.get_by_user(user_id, status)

    async def get_pending_reports(self):
        """Get expense reports pending approval."""
        return await self._report_repo.get_pending_approval()
    
    async def get_standalone_reports(
        self,
        user_id: UUID,
        status: Optional[list[ExpenseReportStatus]] = None,
    ):
        """Get standalone expense reports for a user."""
        return await self._report_repo.get_standalone_reports(user_id, status)

    async def get_admin_expenses_datatable(self, request: DataTableRequest, status: Optional[str] = None):
        """Get expense reports for admin DataTable."""
        # Try to get status from request body if not in query params
        if not status and request.model_extra:
            status = request.model_extra.get("status")
            
        status_list = None
        if status:
            if isinstance(status, str):
                parts = [s.strip() for s in status.split(",") if s.strip()]
                status_list = []
                for s in parts:
                    try:
                        status_list.append(ExpenseReportStatus(s))
                    except ValueError:
                        pass
            elif isinstance(status, list):
                status_list = []
                for s in status:
                    if isinstance(s, str) and s:
                        try:
                            status_list.append(ExpenseReportStatus(s))
                        except ValueError:
                            pass
            
        reports, total, filtered = await self._report_repo.get_datatable(
            request, 
            user_id=None, 
            status=status_list
        )
        
        items = []
        for report in reports:
            user_name = "N/A"
            department = None
            try:
                user_info = await self._auth_client.get_user_info(report.user_id)
                if user_info:
                    user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                    department = user_info.get('department')
            except Exception as e:
                logger.error(f"Error fetching user info for {report.user_id}: {e}")
                pass
            
            # Use Eager loaded trip or fetch it
            trip = report.trip
            
            item = ExpenseAdminDataTableItem(
                id=report.id,
                report_number=report.report_number,
                title=report.title,
                employee_id=report.user_id,
                employee_name=user_name,
                department=department,
                trip_id=report.trip_id,
                trip_title=trip.title if trip else "Generico",
                trip_destination=trip.destination if trip else None,
                trip_start_date=trip.start_date if trip else None,
                trip_end_date=trip.end_date if trip else None,
                total_amount=report.total_amount or Decimal("0"),
                items_count=len(report.items) if report.items is not None else 0,
                status=report.status.value if hasattr(report.status, "value") else str(report.status),
                submitted_at=report.created_at, # Using created_at as fallback
                created_at=report.created_at
            )
            items.append(item)
            
        return items, total, filtered

    async def create_report(self, user_id: UUID, data: ExpenseReportCreate):
        """Create expense report (linked to trip or standalone)."""
        is_standalone = data.is_standalone or data.trip_id is None
        
        # If linked to trip, verify trip exists and belongs to user
        if data.trip_id:
            trip = await self._trip_repo.get(data.trip_id)
            if not trip:
                 raise NotFoundError("Business trip not found")
            if trip.user_id != user_id:
                raise BusinessRuleError("Cannot create report for another user's trip")
        
        # Generate report number
        report_number = await self._report_repo.generate_report_number(
            date.today().year
        )
        
        report = await self._report_repo.create(
            trip_id=data.trip_id,
            is_standalone=is_standalone,
            user_id=user_id,
            report_number=report_number,
            title=data.title,
            period_start=data.period_start,
            period_end=data.period_end,
            employee_notes=data.employee_notes,
            status=ExpenseReportStatus.DRAFT,
            total_amount=Decimal(0),
        )
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="EXPENSE_REPORT",
            resource_id=str(report.id),
            description=f"Created {'standalone ' if is_standalone else ''}report {data.title}",
            request_data=data.model_dump(mode="json"),
        )
        
        await self.db.refresh(report, ["items", "attachments"])
        return report

    async def submit_report(self, id: UUID, user_id: UUID):
        """Submit report for approval."""
        report = await self.get_report(id)
        
        if report.status != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Only draft reports can be submitted")
        
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot submit another user's report")
        
        # Recalculate total
        await self._report_repo.recalculate_total(id)
        
        await self._report_repo.update(id, status=ExpenseReportStatus.SUBMITTED)
        
        # Create approval request
        try:
            user_info = await self._auth_client.get_user_info(user_id)
            requester_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() if user_info else None
            
            await self._approval_client.create_request(
                entity_type="EXPENSE",
                entity_id=id,
                requester_id=user_id,
                title=f"Nota Spese: {report.report_number}",
                entity_ref=report.report_number,
                requester_name=requester_name,
                description=report.employee_notes,
                metadata={
                    "total_amount": float(report.total_amount) if report.total_amount else 0,
                },
                callback_url=f"http://expense-service:8003/api/v1/expenses/internal/approval-callback/{id}",
            )
        except Exception as e:
            # Revert status
            await self._report_repo.update(id, status=ExpenseReportStatus.DRAFT)
            logger.error(f"Failed to create approval request for report {id}: {e}")
            raise BusinessRuleError(f"Failed to submit report: {str(e)}")
        
        await self._audit.log_action(
            user_id=user_id,
            action="SUBMIT",
            resource_type="EXPENSE_REPORT",
            resource_id=str(id),
            description=f"Submitted report {report.report_number}",
        )
        
        return await self.get_report(id)
        
    async def approve_report(self, id: UUID, approver_id: UUID, data: ApproveReportRequest):
        """Approve expense report."""
        report = await self.get_report(id)
        
        if report.status == ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Cannot approve a draft report.")
        
        await self._report_repo.update(
            id,
            status=ExpenseReportStatus.APPROVED,
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=data.notes,
        )
        
        await self._audit.log_action(
            user_id=approver_id,
            action="APPROVE",
            resource_type="EXPENSE_REPORT",
            resource_id=str(id),
            description=f"Approved report {report.report_number}",
            request_data=data.model_dump(mode="json"),
        )
        
        # If linked to wallet (future implementation) or trip management
        # For now, simply notify
        
        await self._send_notification(
            user_id=report.user_id,
            notification_type="report_approved",
            title="Nota spese approvata",
            message=f"La tua nota spese '{report.report_number}' è stata approvata",
            entity_type="ExpenseReport",
            entity_id=str(id),
        )
        
        return await self.get_report(id)

    async def reject_report(self, id: UUID, approver_id: UUID, data: RejectReportRequest):
        """Reject expense report."""
        report = await self.get_report(id)
        
        if report.status == ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Cannot reject a draft report.")
        
        await self._report_repo.update(
            id,
            status=ExpenseReportStatus.REJECTED,
            approver_id=approver_id,
            approver_notes=data.reason,
        )
        
        await self._audit.log_action(
            user_id=approver_id,
            action="REJECT",
            resource_type="EXPENSE_REPORT",
            resource_id=str(id),
            description=f"Rejected report {report.report_number}",
            request_data={"reason": data.reason},
        )
        
        return await self.get_report(id)

    async def mark_paid(self, id: UUID, data: MarkPaidRequest):
        """Mark report as paid."""
        report = await self.get_report(id)
        
        if report.status != ExpenseReportStatus.APPROVED:
            raise BusinessRuleError("Only approved reports can be marked as paid")
            
        await self._report_repo.update(
            id,
            status=ExpenseReportStatus.PAID,
            paid_at=datetime.utcnow(),
            payment_ref=data.payment_reference
        )
        
        await self._audit.log_action(
            user_id=report.user_id, # Should this be the admin who marked it? The caller of this method usually is admin/finance
            action="PAID",
            resource_type="EXPENSE_REPORT",
            resource_id=str(id),
            description=f"Marked report {report.report_number} as paid",
            request_data=data.model_dump(mode="json"),
        )
        
        await self._send_notification(
            user_id=report.user_id,
            notification_type="report_paid",
            title="Nota spese pagata",
            message=f"La tua nota spese '{report.report_number}' è stata messa in pagamento",
            entity_type="ExpenseReport",
            entity_id=str(id),
        )
        
        return await self.get_report(id)

    async def delete_report(self, id: UUID, user_id: UUID):
        """Delete expense report (draft only)."""
        report = await self.get_report(id)
        
        if report.status.lower() != ExpenseReportStatus.DRAFT:
            raise BusinessRuleError("Only draft reports can be deleted")
            
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot delete another user's report")
            
        await self._report_repo.delete(id)
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="EXPENSE_REPORT",
            resource_id=str(id),
            description=f"Deleted report {report.report_number}",
        )
        
        return True

    async def cancel_report(self, id: UUID, user_id: UUID, reason: str):
        """Cancel/Withdraw expense report."""
        report = await self.get_report(id)
        
        if report.status not in [ExpenseReportStatus.SUBMITTED, ExpenseReportStatus.APPROVED]:
            raise BusinessRuleError(f"Cannot cancel report in status {report.status}")
            
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot cancel another user's report")
            
        await self._report_repo.update(id, status=ExpenseReportStatus.CANCELLED)
        
        await self._audit.log_action(
            user_id=user_id,
            action="CANCEL",
            resource_type="EXPENSE_REPORT",
            resource_id=str(id),
            description=f"Cancelled report {report.report_number}. Reason: {reason}",
        )
        
        return await self.get_report(id)

    async def update_report_attachment(
        self, id: UUID, user_id: UUID, content: bytes, filename: str, content_type: str
    ):
        """Upload and update report attachment."""
        report = await self.get_report(id)
        if report.user_id != user_id:
            raise BusinessRuleError("Cannot update another user's report")
        
        # Validation
        if content_type != "application/pdf":
            raise ValidationError("Only PDF files are allowed", field="attachment")
        if len(content) > 5 * 1024 * 1024:
            raise ValidationError("File size exceeds 5MB limit", field="attachment")
        
        # Unique filename
        ext = filename.split(".")[-1]
        storage_filename = f"report_{id}_{datetime.utcnow().timestamp()}.{ext}"
        
        path = storage_manager.upload_file(content, storage_filename, content_type)
        if not path:
            raise BusinessRuleError("Failed to upload file to storage")
            
        # Create attachment record
        attachment = ReportAttachment(
            report_id=id,
            file_path=path,
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
        )
        self.db.add(attachment)
        
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPLOAD_ATTACHMENT",
            resource_type="EXPENSE_REPORT",
            resource_id=str(id),
            description=f"Uploaded attachment {filename} for report {id}",
        )
        
        return await self.get_report(id)
