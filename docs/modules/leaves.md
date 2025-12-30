# Modulo Leaves (Assenze)

## Responsabilità

Il modulo gestisce:
- CRUD Richieste di assenza
- Gestione saldi (balances)
- Workflow approvativo
- Policy Engine per validazione regole
- Calcolo giorni lavorativi

---

## Endpoints API

### Richieste Assenza

| Method | Endpoint | Descrizione | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/leaves` | Lista richieste utente corrente | Employee+ |
| `GET` | `/api/v1/leaves/{id}` | Dettaglio richiesta | Owner/Approver |
| `POST` | `/api/v1/leaves` | Crea nuova richiesta | Employee+ |
| `PUT` | `/api/v1/leaves/{id}` | Modifica richiesta (solo draft) | Owner |
| `DELETE` | `/api/v1/leaves/{id}` | Cancella richiesta | Owner |
| `POST` | `/api/v1/leaves/{id}/submit` | Invia per approvazione | Owner |
| `POST` | `/api/v1/leaves/{id}/cancel` | Annulla richiesta | Owner |

### Approvazioni (Manager/Approver)

| Method | Endpoint | Descrizione | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/leaves/pending` | Lista richieste da approvare | Approver |
| `POST` | `/api/v1/leaves/{id}/approve` | Approva richiesta | Approver |
| `POST` | `/api/v1/leaves/{id}/approve-conditional` | Approva con condizioni | Approver |
| `POST` | `/api/v1/leaves/{id}/reject` | Rifiuta richiesta | Approver |
| `POST` | `/api/v1/leaves/{id}/recall` | Richiama dipendente | HR/Admin |

### Accettazione Condizioni (Employee)

| Method | Endpoint | Descrizione | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/leaves/{id}/accept-conditions` | Accetta condizioni | Owner |

### Saldi

| Method | Endpoint | Descrizione | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/balances` | Saldi utente corrente | Employee+ |
| `GET` | `/api/v1/balances/{user_id}` | Saldi utente specifico | Manager+ |
| `PUT` | `/api/v1/balances/{user_id}` | Rettifica saldi | Admin |

### Calendario

| Method | Endpoint | Descrizione | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/leaves/calendar` | Calendario personale | Employee+ |
| `GET` | `/api/v1/leaves/team-calendar` | Calendario team | Manager+ |

---

## Schemas Pydantic

```python
# schemas.py

from datetime import date, time, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LeaveStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    APPROVED_CONDITIONAL = "approved_conditional"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    RECALLED = "recalled"
    COMPLETED = "completed"


class ApprovalType(str, Enum):
    STANDARD = "standard"
    CONDITIONAL = "conditional"


class ConditionType(str, Enum):
    RIC = "RIC"  # Riserva di Richiamo
    REP = "REP"  # Reperibilità
    PAR = "PAR"  # Approvazione Parziale
    MOD = "MOD"  # Modifica Date
    ALT = "ALT"  # Altra Condizione


# === Request Schemas ===

class LeaveRequestCreate(BaseModel):
    leave_type_id: UUID
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    notes: Optional[str] = None
    inps_protocol: Optional[str] = None  # Solo per malattia


class LeaveRequestUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    notes: Optional[str] = None


class ApproveRequest(BaseModel):
    """Standard approval."""
    pass


class ApproveConditionalRequest(BaseModel):
    """Approval with conditions."""
    condition_type: ConditionType
    conditions: str = Field(..., min_length=10, max_length=1000)


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=1000)


class RecallRequest(BaseModel):
    recall_date: date
    reason: str = Field(..., min_length=10, max_length=1000)


# === Response Schemas ===

class LeaveTypeResponse(BaseModel):
    id: UUID
    code: str
    name: str
    color: str
    
    model_config = {"from_attributes": True}


class LeaveRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: str
    leave_type: LeaveTypeResponse
    start_date: date
    end_date: date
    start_time: Optional[time]
    end_time: Optional[time]
    hours_requested: Optional[Decimal]
    status: LeaveStatus
    approval_type: ApprovalType
    condition_type: Optional[ConditionType]
    approval_conditions: Optional[str]
    conditions_accepted: bool
    approver_id: Optional[UUID]
    approver_name: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    is_recalled: bool
    recall_reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class LeaveBalanceResponse(BaseModel):
    user_id: UUID
    year: int
    vacation_total: Decimal
    vacation_used: Decimal
    vacation_pending: Decimal
    vacation_available: Decimal  # Computed
    vacation_previous_year: Decimal
    rol_total: Decimal
    rol_used: Decimal
    rol_pending: Decimal
    rol_available: Decimal  # Computed
    permits_total: Decimal
    permits_used: Decimal
    permits_pending: Decimal
    permits_available: Decimal  # Computed
    
    model_config = {"from_attributes": True}
```

---

## Service Layer

```python
# service.py

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from src.modules.config.service import ConfigService
from src.modules.leaves.repository import LeaveRepository, BalanceRepository
from src.modules.leaves.schemas import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    ApproveConditionalRequest,
    RejectRequest,
    RecallRequest,
    LeaveStatus,
)
from src.modules.leaves.policy_engine import PolicyEngine
from src.modules.notifications.service import NotificationService


class LeaveService:
    """Business logic for leave requests."""

    def __init__(
        self,
        session: AsyncSession,
        config_service: ConfigService,
        notification_service: NotificationService,
    ) -> None:
        self._repository = LeaveRepository(session)
        self._balance_repository = BalanceRepository(session)
        self._config = config_service
        self._notifications = notification_service
        self._policy_engine = PolicyEngine(config_service)

    async def create_request(
        self,
        user_id: UUID,
        data: LeaveRequestCreate,
    ) -> LeaveRequestResponse:
        """Create a new leave request.
        
        Steps:
        1. Validate against policy rules (min_notice_days, blackout, etc.)
        2. Check balance availability
        3. Check for overlapping requests
        4. Calculate working days/hours
        5. Create request in PENDING status
        6. Update pending balance
        7. Notify approver
        """
        # Get leave type configuration
        leave_type = await self._config.get_leave_type(data.leave_type_id)
        if not leave_type:
            raise NotFoundError("Leave type not found")
        
        # Policy validation
        await self._policy_engine.validate_request(
            user_id=user_id,
            leave_type=leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        
        # Calculate hours/days
        hours = await self._calculate_working_hours(
            user_id=user_id,
            start_date=data.start_date,
            end_date=data.end_date,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        
        # Check balance
        if leave_type.scales_balance:
            await self._check_balance(
                user_id=user_id,
                balance_type=leave_type.balance_type,
                hours_needed=hours,
                allow_negative=leave_type.allow_negative_balance,
            )
        
        # Check overlaps
        await self._check_overlaps(
            user_id=user_id,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        
        # Create request
        request = await self._repository.create(
            user_id=user_id,
            leave_type_id=data.leave_type_id,
            start_date=data.start_date,
            end_date=data.end_date,
            start_time=data.start_time,
            end_time=data.end_time,
            hours_requested=hours,
            notes=data.notes,
            inps_protocol=data.inps_protocol,
            status=LeaveStatus.PENDING if leave_type.requires_approval else LeaveStatus.APPROVED,
        )
        
        # Update pending balance
        if leave_type.scales_balance:
            await self._balance_repository.add_pending(
                user_id=user_id,
                balance_type=leave_type.balance_type,
                hours=hours,
            )
        
        # Notify approver
        if leave_type.requires_approval:
            await self._notifications.notify_new_request(request)
        
        return LeaveRequestResponse.model_validate(request)

    async def approve(
        self,
        request_id: UUID,
        approver_id: UUID,
    ) -> LeaveRequestResponse:
        """Approve a leave request."""
        request = await self._get_request_for_approval(request_id, approver_id)
        
        # Update status
        request = await self._repository.update(
            request_id,
            status=LeaveStatus.APPROVED,
            approver_id=approver_id,
        )
        
        # Move from pending to used balance
        if request.leave_type.scales_balance:
            await self._balance_repository.confirm_pending(
                user_id=request.user_id,
                balance_type=request.leave_type.balance_type,
                hours=request.hours_requested,
            )
        
        # Notify employee
        await self._notifications.notify_approved(request)
        
        return LeaveRequestResponse.model_validate(request)

    async def approve_conditional(
        self,
        request_id: UUID,
        approver_id: UUID,
        data: ApproveConditionalRequest,
    ) -> LeaveRequestResponse:
        """Approve with conditions (needs employee acceptance)."""
        request = await self._get_request_for_approval(request_id, approver_id)
        
        request = await self._repository.update(
            request_id,
            status=LeaveStatus.APPROVED_CONDITIONAL,
            approval_type="conditional",
            condition_type=data.condition_type,
            approval_conditions=data.conditions,
            approver_id=approver_id,
        )
        
        # Notify employee to accept conditions
        await self._notifications.notify_conditional_approval(request)
        
        return LeaveRequestResponse.model_validate(request)

    async def reject(
        self,
        request_id: UUID,
        approver_id: UUID,
        data: RejectRequest,
    ) -> LeaveRequestResponse:
        """Reject a leave request."""
        request = await self._get_request_for_approval(request_id, approver_id)
        
        # Update status
        request = await self._repository.update(
            request_id,
            status=LeaveStatus.REJECTED,
            rejection_reason=data.reason,
            approver_id=approver_id,
        )
        
        # Release pending balance
        if request.leave_type.scales_balance:
            await self._balance_repository.release_pending(
                user_id=request.user_id,
                balance_type=request.leave_type.balance_type,
                hours=request.hours_requested,
            )
        
        # Notify employee
        await self._notifications.notify_rejected(request)
        
        return LeaveRequestResponse.model_validate(request)

    async def recall(
        self,
        request_id: UUID,
        hr_user_id: UUID,
        data: RecallRequest,
    ) -> LeaveRequestResponse:
        """Recall employee from approved leave (HR only)."""
        request = await self._repository.get(request_id)
        if not request:
            raise NotFoundError("Request not found")
        
        if request.status != LeaveStatus.APPROVED:
            raise ValidationError("Can only recall approved requests")
        
        # Calculate hours to refund (from recall_date to end_date)
        hours_to_refund = await self._calculate_working_hours(
            user_id=request.user_id,
            start_date=data.recall_date,
            end_date=request.end_date,
        )
        
        # Update request
        request = await self._repository.update(
            request_id,
            is_recalled=True,
            recall_date=data.recall_date,
            recall_reason=data.reason,
            status=LeaveStatus.RECALLED,
        )
        
        # Refund balance
        if request.leave_type.scales_balance:
            await self._balance_repository.refund(
                user_id=request.user_id,
                balance_type=request.leave_type.balance_type,
                hours=hours_to_refund,
            )
        
        # Create expense report for reimbursement
        await self._create_recall_expense_report(request)
        
        # Notify employee
        await self._notifications.notify_recalled(request)
        
        return LeaveRequestResponse.model_validate(request)
```

---

## Policy Engine

```python
# policy_engine.py

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from src.core.exceptions import ValidationError
from src.modules.config.service import ConfigService


class PolicyEngine:
    """Validates leave requests against configurable rules."""

    def __init__(self, config_service: ConfigService) -> None:
        self._config = config_service

    async def validate_request(
        self,
        user_id: UUID,
        leave_type: Any,  # LeaveType model
        start_date: date,
        end_date: date,
    ) -> None:
        """Run all policy validations.
        
        Raises:
            ValidationError: If any rule is violated.
        """
        await self._validate_date_range(start_date, end_date)
        await self._validate_min_notice(leave_type, start_date)
        await self._validate_max_consecutive(leave_type, start_date, end_date)
        await self._validate_past_dates(leave_type, start_date)
        await self._validate_blackout_dates(leave_type, start_date, end_date)
        await self._validate_monthly_limit(user_id, leave_type, start_date)

    async def _validate_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> None:
        """Ensure start_date <= end_date."""
        if start_date > end_date:
            raise ValidationError("La data di inizio deve essere precedente alla data di fine")

    async def _validate_min_notice(
        self,
        leave_type: Any,
        start_date: date,
    ) -> None:
        """Check minimum notice days.
        
        Example: ROL requires 2 days notice (can't request for today or tomorrow).
        """
        if leave_type.min_notice_days is None or leave_type.min_notice_days == 0:
            return
        
        today = date.today()
        min_start = today + timedelta(days=leave_type.min_notice_days)
        
        if start_date < min_start:
            raise ValidationError(
                f"Per {leave_type.name} è richiesto un preavviso minimo di "
                f"{leave_type.min_notice_days} giorni. "
                f"La prima data disponibile è {min_start.strftime('%d/%m/%Y')}"
            )

    async def _validate_max_consecutive(
        self,
        leave_type: Any,
        start_date: date,
        end_date: date,
    ) -> None:
        """Check maximum consecutive days."""
        if leave_type.max_consecutive_days is None:
            return
        
        days_requested = (end_date - start_date).days + 1
        
        if days_requested > leave_type.max_consecutive_days:
            raise ValidationError(
                f"Per {leave_type.name} il massimo di giorni consecutivi è "
                f"{leave_type.max_consecutive_days}. Hai richiesto {days_requested} giorni."
            )

    async def _validate_past_dates(
        self,
        leave_type: Any,
        start_date: date,
    ) -> None:
        """Check if past dates are allowed (usually only for sickness)."""
        today = date.today()
        
        if start_date < today and not leave_type.allow_past_dates:
            raise ValidationError(
                f"Non è possibile richiedere {leave_type.name} per date passate"
            )

    async def _validate_blackout_dates(
        self,
        leave_type: Any,
        start_date: date,
        end_date: date,
    ) -> None:
        """Check against blackout periods (from config)."""
        # Load blackout dates from config
        blackout_key = f"leave.blackout_dates.{leave_type.code.lower()}"
        blackout_dates = await self._config.get(blackout_key, default=[])
        
        if not blackout_dates:
            return
        
        # Check overlap
        current = start_date
        while current <= end_date:
            if current.isoformat() in blackout_dates:
                raise ValidationError(
                    f"La data {current.strftime('%d/%m/%Y')} non è disponibile per {leave_type.name}"
                )
            current += timedelta(days=1)

    async def _validate_monthly_limit(
        self,
        user_id: UUID,
        leave_type: Any,
        start_date: date,
    ) -> None:
        """Check monthly limits (e.g., L.104 max 3 days/month)."""
        if leave_type.max_per_month is None:
            return
        
        # TODO: Query existing requests for the month
        # and check if adding this would exceed limit
        pass
```

---

## Stati Workflow

```
                                    ┌──────────────────┐
                                    │ APPROVED_COND    │
                                    │ (Needs Accept)   │
                                    └────────┬─────────┘
                                             │ accept_conditions()
                                             v
┌────────┐    submit()    ┌─────────┐   approve()   ┌──────────┐    (auto)    ┌───────────┐
│ DRAFT  │ ─────────────> │ PENDING │ ────────────> │ APPROVED │ ───────────> │ COMPLETED │
└────────┘                └─────────┘               └──────────┘              └───────────┘
    │                          │                         │
    │ delete()                 │ reject()                │ recall()
    v                          v                         v
┌────────┐                ┌──────────┐              ┌──────────┐
│ (gone) │                │ REJECTED │              │ RECALLED │
└────────┘                └──────────┘              └──────────┘
                               │
    ┌──────────────────────────┘
    │ cancel() (owner, before approval)
    v
┌───────────┐
│ CANCELLED │
└───────────┘
```

### Transizioni Ammesse

| From | To | Action | Actor |
|------|-----|--------|-------|
| DRAFT | PENDING | submit | Owner |
| DRAFT | (deleted) | delete | Owner |
| PENDING | APPROVED | approve | Approver |
| PENDING | APPROVED_CONDITIONAL | approve_conditional | Approver |
| PENDING | REJECTED | reject | Approver |
| PENDING | CANCELLED | cancel | Owner |
| APPROVED_CONDITIONAL | APPROVED | accept_conditions | Owner |
| APPROVED_CONDITIONAL | CANCELLED | cancel (refuse conditions) | Owner |
| APPROVED | COMPLETED | (automatic, date passed) | System |
| APPROVED | RECALLED | recall | HR |
| APPROVED | CANCELLED | cancel (needs approval) | Owner+Approver |
