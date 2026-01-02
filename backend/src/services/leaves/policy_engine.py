from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessRuleError
from src.services.leaves.schemas import PolicyValidationResult
from src.services.leaves.models import LeaveRequestStatus
from src.services.leaves.repository import LeaveRequestRepository
from src.shared.clients import ConfigClient
from src.services.leaves.balance_service import LeaveBalanceService

class PolicyEngine:
    """Engine for validating leave requests against business rules."""

    def __init__(
        self,
        session: AsyncSession,
        leave_request_repo: LeaveRequestRepository,
        balance_service: LeaveBalanceService,
        config_client: Optional[ConfigClient] = None,
    ) -> None:
        self._session = session
        self._request_repo = leave_request_repo
        self._balance_service = balance_service
        self._config_client = config_client or ConfigClient()
        self._config_cache: dict = {}

    async def _get_leave_type(self, leave_type_id: UUID) -> Optional[dict]:
        """Get leave type from ConfigService."""
        cache_key = f"leave_type_{leave_type_id}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        data = await self._config_client.get_leave_type(leave_type_id)
        if data:
            self._config_cache[cache_key] = data
            return data
        return None

    async def validate_request(
        self,
        user_id: UUID,
        leave_type_id: UUID,
        start_date: date,
        end_date: date,
        days_requested: Decimal,
        exclude_request_id: Optional[UUID] = None,
    ) -> PolicyValidationResult:
        """Validate a leave request against all policy rules."""
        errors: list[str] = []
        warnings: list[str] = []
        
        leave_type = await self._get_leave_type(leave_type_id)
        if not leave_type:
            return PolicyValidationResult(is_valid=False, errors=["Leave type not found"])
        
        code = leave_type.get("code", "")
        
        # Notice Period
        min_notice = leave_type.get("min_notice_days")
        if min_notice and not leave_type.get("allow_past_dates", False):
            today = date.today()
            notice_days = (start_date - today).days
            if notice_days < min_notice:
                errors.append(f"Preavviso minimo di {min_notice} giorni richiesto. Attuale: {notice_days}.")
        
        # Max Consecutive
        max_consecutive = leave_type.get("max_consecutive_days")
        if max_consecutive and days_requested > max_consecutive:
            errors.append(f"Superato limite massimo di {max_consecutive} giorni consecutivi.")
        
        # Overlap check
        overlapping = await self._request_repo.check_overlap(
            user_id=user_id, start_date=start_date, end_date=end_date, exclude_id=exclude_request_id
        )
        if overlapping:
            errors.append("Sottrazione: esistono già richieste per le date selezionate.")
        
        # Balance check
        balance_sufficient = True
        balance_breakdown = {}
        
        if leave_type.get("scales_balance", False):
            balance_type = leave_type.get("balance_type")
            summary = await self._balance_service.get_balance_summary(user_id, start_date.year)
            
            if balance_type == "vacation":
                # For validation, we use available which already accounts for pending
                # Wait, does get_balance_summary.vacation_available account for pending?
                # Let's check my implementation:
                # vacation_available = vac_total (confirmed)
                # I should probably subtract pending locally if I want strictly "available for NEW request"
                available = summary.vacation_available - summary.vacation_pending
                
                if days_requested > available and not leave_type.get("allow_negative_balance", False):
                    balance_sufficient = False
                    errors.append(f"Saldo ferie insufficiente. Disponibile (netto pendenti): {available}gg.")
                
                # We pass 'vacation' to breakdown, WalletService will handle the FIFO
                balance_breakdown = {"vacation": float(days_requested)}
                
            elif balance_type == "rol":
                available = summary.rol_available - summary.rol_pending
                hours_requested = days_requested * 8
                if hours_requested > available and not leave_type.get("allow_negative_balance", False):
                    balance_sufficient = False
                    errors.append(f"Saldo ROL insufficiente. Disponibile (netto pendenti): {available}h.")
                balance_breakdown = {"rol": float(hours_requested)}

            elif balance_type == "permits":
                available = summary.permits_available - summary.permits_pending
                hours_requested = days_requested * 8
                if hours_requested > available and not leave_type.get("allow_negative_balance", False):
                    balance_sufficient = False
                    errors.append(f"Saldo permessi insufficiente. Disponibile (netto pendenti): {available}h.")
                balance_breakdown = {"permits": float(hours_requested)}

        return PolicyValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            requires_approval=leave_type.get("requires_approval", True),
            balance_sufficient=balance_sufficient,
            balance_breakdown=balance_breakdown,
        )
