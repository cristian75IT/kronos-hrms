"""
KRONOS - Expense Service - Trips Module

Handles Business Trip management, workflow, and attachments.
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.services.expenses.models import TripStatus, TripAttachment
from src.services.expenses.schemas import (
    BusinessTripCreate,
    BusinessTripUpdate,
    ApproveTripRequest,
    RejectTripRequest,
    TripDataTableRequest,
    TripAdminDataTableItem,
    ApprovalCallback,
)
from src.shared.schemas import DataTableRequest
from src.shared.storage import storage_manager
from src.services.expenses.services.base import BaseExpenseService

logger = logging.getLogger(__name__)


class ExpenseTripService(BaseExpenseService):
    """
    Sub-service for Business Trip management.
    """

    async def get_trip(self, id: UUID):
        """Get trip by ID."""
        trip = await self._trip_repo.get(id)
        if not trip:
            raise NotFoundError("Business trip not found", entity_type="BusinessTrip", entity_id=str(id))
        return trip

    async def get_user_trips(
        self,
        user_id: UUID,
        status: Optional[list[TripStatus]] = None,
        year: Optional[int] = None,
    ):
        """Get trips for a user."""
        return await self._trip_repo.get_by_user(user_id, status, year)

    async def get_pending_trips(self):
        """Get trips pending approval."""
        return await self._trip_repo.get_pending_approval()

    async def get_trips_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[TripStatus]] = None,
    ):
        """Get trips for DataTable."""
        return await self._trip_repo.get_datatable(request, user_id, status)

    async def get_admin_trips_datatable(self, request: TripDataTableRequest):
        """Get trips for admin DataTable."""
        status_list = None
        if request.status:
            status_list = [TripStatus(s.strip()) for s in request.status.split(",")]
            
        trips, total, filtered = await self._trip_repo.get_datatable(
            request, 
            user_id=None, 
            status=status_list
        )
        
        items = []
        for trip in trips:
            days = (trip.end_date - trip.start_date).days + 1
            
            user_name = "N/A"
            try:
                user_info = await self._auth_client.get_user_info(trip.user_id)
                if user_info:
                    user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            except Exception:
                pass
            
            item = TripAdminDataTableItem.model_validate(trip)
            item.user_name = user_name
            item.days_count = days
            item.total_allowance = trip.estimated_budget or Decimal(0)
            
            items.append(item)
            
        return items, total, filtered
        
    async def get_active_trips_for_date(self, target_date: date):
        """Get all approved/active trips for a specific date across all users."""
        return await self._trip_repo.get_active_trips_for_date(target_date)

    async def create_trip(self, user_id: UUID, data: BusinessTripCreate):
        """Create new business trip."""
        trip = await self._trip_repo.create(
            user_id=user_id,
            status=TripStatus.DRAFT,
            **data.model_dump(),
        )
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="BUSINESS_TRIP",
            resource_id=str(trip.id),
            description=f"Created trip {trip.title}",
            request_data=data.model_dump(mode="json"),
        )
        
        await self.db.refresh(trip, ["attachments", "daily_allowances", "expense_reports"])
        return trip

    async def update_trip(self, id: UUID, user_id: UUID, data: BusinessTripUpdate):
        """Update trip (draft only)."""
        trip = await self.get_trip(id)
        
        if trip.status != TripStatus.DRAFT:
            raise BusinessRuleError("Only draft trips can be updated")
        
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot update another user's trip")
        
        updated_trip = await self._trip_repo.update(id, **data.model_dump(exclude_unset=True))

        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Updated trip {trip.title}",
            request_data=data.model_dump(mode="json"),
        )

        return updated_trip

    async def submit_trip(self, id: UUID, user_id: UUID):
        """Submit trip for approval."""
        trip = await self.get_trip(id)
        
        if trip.status != TripStatus.DRAFT:
            raise BusinessRuleError("Only draft trips can be submitted")
        
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot submit another user's trip")
        
        await self._trip_repo.update(id, status=TripStatus.PENDING)
        
        await self._audit.log_action(
            user_id=user_id,
            action="SUBMIT",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Submitted trip {trip.title}",
        )
        
        # Create approval request
        try:
            user_info = await self._auth_client.get_user_info(user_id)
            requester_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() if user_info else None
            
            await self._approval_client.create_request(
                entity_type="TRIP",
                entity_id=id,
                requester_id=user_id,
                title=f"Trasferta: {trip.title}",
                entity_ref=trip.project_code or f"TRIP-{str(trip.id)[:8]}",
                requester_name=requester_name,
                description=trip.description,
                metadata={
                    "destination": trip.destination,
                    "start_date": trip.start_date.isoformat(),
                    "end_date": trip.end_date.isoformat(),
                    "estimated_budget": float(trip.estimated_budget) if trip.estimated_budget else 0,
                },
                callback_url=f"http://expense-service:8003/api/v1/expenses/internal/approval-callback/{id}",
            )
        except Exception as e:
            # Revert status
            await self._trip_repo.update(id, status=TripStatus.DRAFT)
            logger.error(f"Failed to create approval request for trip {id}: {e}")
            raise BusinessRuleError(f"Failed to submit trip: {str(e)}")
        
        return await self.get_trip(id)

    async def approve_trip(self, id: UUID, approver_id: UUID, data: ApproveTripRequest, generate_allowances_callback=None):
        """
        Approve trip.
        
        :param generate_allowances_callback: Optional async function to generate allowances (to avoid circular dependency)
        """
        trip = await self.get_trip(id)
        
        if trip.status == TripStatus.DRAFT:
            raise BusinessRuleError("Cannot approve a draft trip. It must be submitted first.")
        
        await self._trip_repo.update(
            id,
            status=TripStatus.APPROVED,
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=data.notes,
        )
        
        await self._audit.log_action(
            user_id=approver_id,
            action="APPROVE",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Approved trip {trip.title}",
            request_data=data.model_dump(mode="json"),
        )
        
        # Auto-generate daily allowances if callback provided
        if generate_allowances_callback:
            await generate_allowances_callback(id)
        
        # Initialize Trip Wallet
        budget = trip.estimated_budget or Decimal(0)
        try:
            await self._wallet_service.create_wallet(id, trip.user_id, budget)
        except Exception as e:
            logger.error(f"Failed to initialize local wallet for trip {id}: {e}")
        
        # Send notification to employee
        await self._send_notification(
            user_id=trip.user_id,
            notification_type="trip_approved",
            title="Trasferta approvata",
            message=f"La tua trasferta '{trip.title}' è stata approvata",
            entity_type="BusinessTrip",
            entity_id=str(id),
        )
        
        return await self.get_trip(id)

    async def reject_trip(self, id: UUID, approver_id: UUID, data: RejectTripRequest):
        """Reject trip."""
        trip = await self.get_trip(id)
        
        if trip.status == TripStatus.DRAFT:
            raise BusinessRuleError("Cannot reject a draft trip.")
        
        await self._trip_repo.update(
            id,
            status=TripStatus.REJECTED,
            approver_id=approver_id,
            approver_notes=data.reason,
        )
        
        # Audit Log
        await self._audit.log_action(
            user_id=approver_id,
            action="REJECT",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Rejected trip {trip.title}",
            request_data={"reason": data.reason},
        )
        
        return await self.get_trip(id)

    async def complete_trip(self, id: UUID, user_id: UUID):
        """Mark trip as completed."""
        trip = await self.get_trip(id)
        
        if trip.status.lower() != TripStatus.APPROVED:
            raise BusinessRuleError("Only approved trips can be completed")
            
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot complete another user's trip")
            
        await self._trip_repo.update(id, status=TripStatus.COMPLETED)
        
        await self._audit.log_action(
            user_id=user_id,
            action="COMPLETE",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Completed trip {trip.title}",
        )
        
        return await self.get_trip(id)

    async def delete_trip(self, id: UUID, user_id: UUID):
        """Delete trip (draft only)."""
        trip = await self.get_trip(id)
        
        if trip.status.lower() != TripStatus.DRAFT:
            raise BusinessRuleError("Only draft trips can be deleted")
            
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot delete another user's trip")
            
        await self._trip_repo.delete(id)
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Deleted trip {trip.title}",
        )
        
        return True

    async def cancel_trip(self, id: UUID, user_id: UUID, reason: str):
        """Cancel/Withdraw trip request."""
        trip = await self.get_trip(id)
        
        # Can cancel if pending or approved (if not already completed)
        if trip.status.lower() not in [TripStatus.PENDING, TripStatus.SUBMITTED, TripStatus.APPROVED]:
            raise BusinessRuleError(f"Cannot cancel trip in status {trip.status}")
            
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot cancel another user's trip")
            
        await self._trip_repo.update(id, status=TripStatus.CANCELLED)
        
        await self._audit.log_action(
            user_id=user_id,
            action="CANCEL",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Cancelled trip {trip.title}. Reason: {reason}",
        )
        
        return await self.get_trip(id)

    async def update_trip_attachment(
        self, id: UUID, user_id: UUID, content: bytes, filename: str, content_type: str
    ):
        """Upload and update trip attachment."""
        trip = await self.get_trip(id)
        if trip.user_id != user_id:
            raise BusinessRuleError("Cannot update another user's trip")
        
        # Validation
        if content_type != "application/pdf":
            raise ValidationError("Only PDF files are allowed", field="attachment")
        if len(content) > 2 * 1024 * 1024:
            raise ValidationError("File size exceeds 2MB limit", field="attachment")
        
        # Unique filename
        ext = filename.split(".")[-1]
        storage_filename = f"trip_{id}_{datetime.utcnow().timestamp()}.{ext}"
        
        path = storage_manager.upload_file(content, storage_filename, content_type)
        if not path:
            raise BusinessRuleError("Failed to upload file to storage")
            
        # Create attachment record
        attachment = TripAttachment(
            trip_id=id,
            file_path=path,
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
        )
        self.db.add(attachment)
        
        # Update legacy path for compatibility
        trip.attachment_path = path
        
        await self.db.commit()
        
        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="UPLOAD_ATTACHMENT",
            resource_type="BUSINESS_TRIP",
            resource_id=str(id),
            description=f"Uploaded attachment {filename} for trip {id}",
        )
        
        return await self.get_trip(id)

    async def handle_approval_callback(self, data: ApprovalCallback, approve_callback=None, reject_callback=None):
        """
        Handle approval callback.
        delegates to approve/reject methods which are provided as callbacks if needed
        or calls internal methods if they are self-contained.
        
        Actually, since this class has approve_trip/reject_trip, we can call them directly.
        BUT for expense reports, we might need callbacks or just splitting the logic.
        
        This method should only handle TRIP callbacks if this is the Trips Service.
        The main facade will route to the correct service.
        """
        pass # Implemented in Façade or specific service logic. 
             # We'll put specific logic in each service.
