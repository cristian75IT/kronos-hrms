"""
KRONOS - Smart Working Service
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessRuleError, NotFoundError, ConflictError
from src.core.config import settings
from src.services.smart_working.models import (
    SWAgreement, SWAgreementStatus,
    SWRequest, SWRequestStatus,
    SWAttendance
)
from src.services.smart_working.schemas import (
    SWAgreementCreate, SWAgreementUpdate,
    SWRequestCreate,
    SWAttendanceCheckIn, SWAttendanceCheckOut,
    ApprovalCallback, SWPresenceCreate
)
from src.services.smart_working.repository import SmartWorkingRepository
from src.shared.clients.approval import ApprovalClient
from src.shared.clients.config import ConfigClient
from src.shared.audit_client import get_audit_logger

import logging

logger = logging.getLogger(__name__)

class SmartWorkingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = SmartWorkingRepository(session)
        self._approval_client = ApprovalClient()
        self._config_client = ConfigClient()
        self._audit = get_audit_logger("smart-working")

    # -----------------------------------------------------------------------
    # Agreements
    # -----------------------------------------------------------------------

    async def create_agreement(self, data: SWAgreementCreate, created_by: UUID) -> SWAgreement:
        """
        Create a new Smart Working Agreement.
        
        Historization: Any existing active agreements for this user are automatically
        expired (end_date = day before new start_date, status = EXPIRED).
        """
        # 1. Auto-expire existing active agreements (Historization)
        existing_active = await self._repo.get_active_agreements_for_user(data.user_id)
        expired_count = 0
        
        for existing in existing_active:
            existing.status = SWAgreementStatus.EXPIRED
            existing.end_date = data.start_date - timedelta(days=1)
            await self._repo.update_agreement(existing)
            expired_count += 1
            
            await self._audit.log_action(
                user_id=created_by,
                action="AUTO_EXPIRE_AGREEMENT",
                resource_type="SW_AGREEMENT",
                resource_id=str(existing.id),
                description=f"Auto-expired due to new agreement creation"
            )

        # 2. Create new agreement
        agreement = SWAgreement(
            user_id=data.user_id,
            start_date=data.start_date,
            end_date=data.end_date,
            allowed_days_per_week=data.allowed_days_per_week,
            allowed_weekdays=data.allowed_weekdays,
            status=SWAgreementStatus.ACTIVE,
            notes=data.notes,
            metadata_fields=data.metadata_fields,
            created_by=created_by
        )
        
        await self._repo.create_agreement(agreement)
        
        await self._audit.log_action(
            user_id=created_by,
            action="CREATE_AGREEMENT",
            resource_type="SW_AGREEMENT",
            resource_id=str(agreement.id),
            description=f"Created Smart Working Agreement for user {data.user_id}" + 
                        (f" (expired {expired_count} previous)" if expired_count else "")
        )
        
        return agreement

    async def get_user_agreements(self, user_id: UUID) -> List[SWAgreement]:
        return await self._repo.get_user_agreements(user_id)

    async def update_agreement(self, agreement_id: UUID, data: SWAgreementCreate, updated_by: UUID) -> SWAgreement:
        agreement = await self._repo.get_agreement(agreement_id)
        if not agreement:
            raise NotFoundError("Agreement not found")
        
        agreement.start_date = data.start_date
        agreement.end_date = data.end_date
        agreement.allowed_days_per_week = data.allowed_days_per_week
        agreement.allowed_weekdays = data.allowed_weekdays
        agreement.notes = data.notes
        if data.metadata_fields:
            agreement.metadata_fields = data.metadata_fields
        
        await self._repo.update_agreement(agreement)
        
        await self._audit.log_action(
            user_id=updated_by,
            action="UPDATE_AGREEMENT",
            resource_type="SW_AGREEMENT",
            resource_id=str(agreement.id),
            description=f"Updated Smart Working Agreement for user {agreement.user_id}"
        )
        
        return agreement

    async def terminate_agreement(self, agreement_id: UUID, user_id: UUID) -> SWAgreement:
        agreement = await self._repo.get_agreement(agreement_id)
        if not agreement:
            raise NotFoundError("Agreement not found")
        
        agreement.status = SWAgreementStatus.TERMINATED
        agreement.end_date = date.today()
        await self._repo.update_agreement(agreement)
        
        await self._audit.log_action(
            user_id=user_id,
            action="TERMINATE_AGREEMENT",
            resource_type="SW_AGREEMENT",
            resource_id=str(agreement.id),
            description="Terminated Smart Working Agreement"
        )
        
        return agreement

    # -----------------------------------------------------------------------
    # Requests
    # -----------------------------------------------------------------------

    async def submit_request(self, data: SWRequestCreate, user_id: UUID) -> SWRequest:
        # 1. Check Agreement
        agreement = await self._repo.get_agreement(data.agreement_id)
        if not agreement:
            raise NotFoundError("Agreement not found")
        
        if agreement.user_id != user_id:
            raise BusinessRuleError("Agreement belongs to another user")
            
        if agreement.status != SWAgreementStatus.ACTIVE:
            raise BusinessRuleError("Agreement is not active")
            
        if data.date < agreement.start_date or (agreement.end_date and data.date > agreement.end_date):
            raise BusinessRuleError("Date is outside agreement validity period")

        # 2. Check Valid Day (Not weekend)
        request_weekday = data.date.weekday()
        if request_weekday >= 5:  # 5=Sat, 6=Sun
            raise BusinessRuleError("Smart Working non è consentito nel weekend")

        # 3. Check Allowed Weekdays (if restrictions exist)
        if agreement.allowed_weekdays:
            if request_weekday not in agreement.allowed_weekdays:
                weekday_names = {0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì", 4: "Venerdì"}
                allowed_names = [weekday_names.get(d, str(d)) for d in agreement.allowed_weekdays]
                requested_name = weekday_names.get(request_weekday, str(request_weekday))
                raise BusinessRuleError(
                    f"Smart Working non consentito di {requested_name}. "
                    f"Giorni permessi: {', '.join(allowed_names)}"
                )

        # 3. Check Duplicates
        existing = await self._repo.get_request_by_date(user_id, data.date)
        if existing:
            raise BusinessRuleError(f"Request already exists for date {data.date}")

        # 4. Check Weekly Limit
        start_of_week = data.date - timedelta(days=data.date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        count_week = await self._repo.get_requests_in_week(user_id, start_of_week, end_of_week)
        if count_week >= agreement.allowed_days_per_week:
            raise BusinessRuleError(f"Weekly limit of {agreement.allowed_days_per_week} days reached")

        # 5. Create Request
        # Check config for auto-approval? Assuming approval required for now.
        requires_approval = True # Can be config driven
        
        request = SWRequest(
            user_id=user_id,
            agreement_id=agreement.id,
            date=data.date,
            status=SWRequestStatus.PENDING if requires_approval else SWRequestStatus.APPROVED,
            notes=data.notes
        )
        
        await self._repo.create_request(request)
        
        # 6. Trigger Approval Workflow
        if requires_approval:
            approval_id = await self._approval_client.create_request(
                entity_type="SMART_WORKING",
                entity_id=request.id,
                requester_id=user_id,
                title=f"Smart Working: {data.date}",
                entity_ref="SW",
                description=data.notes or "Lavoro Agile",
                metadata={
                    "date": data.date.isoformat(),
                    "agreement_id": str(agreement.id)
                },
                callback_url=f"{settings.smart_working_service_url}/api/v1/smart-working/internal/approval-callback/{request.id}"
            )
            request.approval_request_id = approval_id
            await self._repo.update_request(request)

        await self._audit.log_action(
            user_id=user_id,
            action="SUBMIT_REQUEST",
            resource_type="SW_REQUEST",
            resource_id=str(request.id),
            description=f"Submitted SW request for {data.date}"
        )

        return request

    async def get_user_requests(self, user_id: UUID) -> List[SWRequest]:
        return await self._repo.get_user_requests(user_id)

    async def cancel_request(self, request_id: UUID, user_id: UUID) -> SWRequest:
        request = await self._repo.get_request(request_id)
        if not request:
            raise NotFoundError("Request not found")
            
        if request.user_id != user_id:
            raise BusinessRuleError("Cannot cancel another user's request")
            
        if request.status == SWRequestStatus.CANCELLED:
             return request
             
        if request.date < date.today():
             raise BusinessRuleError("Cannot cancel past requests")

        request.status = SWRequestStatus.CANCELLED
        await self._repo.update_request(request)
        
        # Cancel approval if pending
        if request.approval_request_id:
            try:
                await self._approval_client.cancel_request(request.approval_request_id, user_id, "Cancelled by user")
            except Exception as e:
                logger.warning(f"Failed to cancel approval request: {e}")

        await self._audit.log_action(
            user_id=user_id,
            action="CANCEL_REQUEST",
            resource_type="SW_REQUEST",
            resource_id=str(request.id),
            description="Cancelled SW request"
        )
        # Avoid lazy load error during serialization
        request.attendance = None
        return request

    async def submit_presence(self, data: SWPresenceCreate, user_id: UUID) -> SWRequest:
        """
        Submit a 'Presence' declaration (cancels any automatic SW for that day).
        Effectively creates a CANCELLED request with specific notes.
        """
        # 1. Check if dates are valid
        if data.date < date.today():
             raise BusinessRuleError("Cannot declare presence for past dates")
             
        # 2. Check if request already exists (using specific query to find even cancelled ones to avoid duplicates)
        # However, repo.get_request_by_date excludes Cancelled. 
        # For now we accept duplicates or better: we should check recent requests.
        
        # Check active first (Priority: if I have a PENDING request, this cancels it)
        existing = await self._repo.get_request_by_date(user_id, data.date)
        if existing:
            # If it's pending/approved, we are effectively cancelling it
            if existing.status in [SWRequestStatus.PENDING, SWRequestStatus.APPROVED]:
                 return await self.cancel_request(existing.id, user_id)
        
        # 3. Create new request as CANCELLED directly
        # We need an agreement ID to link to, find active one
        agreements = await self._repo.get_active_agreements_for_user(user_id)
        if not agreements:
            raise BusinessRuleError("No active Smart Working agreement found")
            
        agreement = agreements[0] # Take first active
        
        request = SWRequest(
            user_id=user_id,
            agreement_id=agreement.id,
            date=data.date,
            status=SWRequestStatus.CANCELLED,
            notes="Lavoro in presenza"
        )
        
        await self._repo.create_request(request)
        
        await self._audit.log_action(
            user_id=user_id,
            action="DECLARE_PRESENCE",
            resource_type="SW_REQUEST",
            resource_id=str(request.id),
            description=f"Declared presence on SW day {data.date}"
        )
        
        # Avoid lazy load error
        request.attendance = None
        
        return request


    # -----------------------------------------------------------------------
    # Approval Callbacks
    # -----------------------------------------------------------------------

    async def handle_approval_callback(self, request_id: UUID, data: ApprovalCallback):
        request = await self._repo.get_request(request_id)
        if not request:
            logger.error(f"Callback found no request {request_id}")
            return

        # Check existing status to avoid duplicates/race conditions
        if request.status in [SWRequestStatus.APPROVED, SWRequestStatus.REJECTED]:
            logger.info(f"Request {request_id} already matched status {request.status}")
            return

        if data.status == "APPROVED":
            request.status = SWRequestStatus.APPROVED
            request.approved_at = datetime.utcnow()
            request.approver_id = data.final_decision_by
        elif data.status == "REJECTED":
            request.status = SWRequestStatus.REJECTED
            request.rejection_reason = data.resolution_notes
            request.approver_id = data.final_decision_by
        
        await self._repo.update_request(request)
        logger.info(f"Updated SW Request {request_id} via callback to {data.status}")

    # -----------------------------------------------------------------------
    # Attendance
    # -----------------------------------------------------------------------

    async def check_in(self, data: SWAttendanceCheckIn, user_id: UUID) -> SWAttendance:
        # Check feature flag
        is_enabled = await self._config_client.get_sys_config("smart_working.attendance_enabled", False)
        if not is_enabled:
            raise BusinessRuleError("Smart Working attendance tracking is disabled")

        request = await self._repo.get_request(data.request_id)
        if not request or request.user_id != user_id:
            raise NotFoundError("Request not found")

        if request.status != SWRequestStatus.APPROVED:
            raise BusinessRuleError("Request must be approved to check in")
            
        if request.date != date.today():
            raise BusinessRuleError("Can only check in on the request date")

        existing = await self._repo.get_attendance(request.id)
        if existing:
            raise BusinessRuleError("Check-in already recorded")

        attendance = SWAttendance(
            request_id=request.id,
            check_in=datetime.utcnow(),
            location=data.location
        )
        
        await self._repo.create_attendance(attendance)
        return attendance

    async def check_out(self, data: SWAttendanceCheckOut, user_id: UUID) -> SWAttendance:
        attendance = await self._repo.get_attendance(data.request_id)
        if not attendance:
            raise NotFoundError("Check-in not found")
            
        request = await self._repo.get_request(attendance.request_id)
        if request.user_id != user_id:
             raise BusinessRuleError("Unauthorized")

        if attendance.check_out:
             raise BusinessRuleError("Check-out already recorded")
             
        attendance.check_out = datetime.utcnow()
        await self._repo.update_attendance(attendance)
        return attendance
