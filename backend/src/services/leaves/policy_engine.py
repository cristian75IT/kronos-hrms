"""KRONOS Leave Service - Policy Engine."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import BusinessRuleError, InsufficientBalanceError
from src.services.leaves.schemas import PolicyValidationResult
from src.services.leaves.models import LeaveRequestStatus
from src.services.leaves.repository import LeaveRequestRepository, LeaveBalanceRepository


class PolicyEngine:
    """Engine for validating leave requests against business rules.
    
    Rules are loaded from ConfigService (database) - no hardcoding.
    """

    def __init__(
        self,
        session: AsyncSession,
        leave_request_repo: LeaveRequestRepository,
        balance_repo: LeaveBalanceRepository,
    ) -> None:
        self._session = session
        self._request_repo = leave_request_repo
        self._balance_repo = balance_repo
        self._config_cache: dict = {}

    async def _get_config(self, key: str, default: any = None) -> any:
        """Get config value from ConfigService."""
        if key in self._config_cache:
            return self._config_cache[key]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.config_service_url}/api/v1/config/{key}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    self._config_cache[key] = data.get("value", default)
                    return self._config_cache[key]
        except Exception:
            pass
        
        return default

    async def _get_leave_type(self, leave_type_id: UUID) -> Optional[dict]:
        """Get leave type from ConfigService."""
        cache_key = f"leave_type_{leave_type_id}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.config_service_url}/api/v1/leave-types/{leave_type_id}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    self._config_cache[cache_key] = data
                    return data
        except Exception:
            pass
        
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
        """Validate a leave request against all policy rules.
        
        Args:
            user_id: ID of the employee
            leave_type_id: ID of leave type
            start_date: Start date of leave
            end_date: End date of leave
            days_requested: Number of days requested
            exclude_request_id: Exclude this request from overlap check (for updates)
            
        Returns:
            PolicyValidationResult with validation status
        """
        errors: list[str] = []
        warnings: list[str] = []
        
        # Get leave type configuration
        leave_type = await self._get_leave_type(leave_type_id)
        if not leave_type:
            return PolicyValidationResult(
                is_valid=False,
                errors=["Leave type not found"],
            )
        
        code = leave_type.get("code", "")
        
        # ─────────────────────────────────────────────────────────────
        # Rule 1: Check minimum notice period
        # ─────────────────────────────────────────────────────────────
        min_notice = leave_type.get("min_notice_days")
        if min_notice and not leave_type.get("allow_past_dates", False):
            today = date.today()
            notice_days = (start_date - today).days
            
            if notice_days < min_notice:
                errors.append(
                    f"Richiesta richiede preavviso minimo di {min_notice} giorni. "
                    f"Preavviso attuale: {notice_days} giorni."
                )
        
        # ─────────────────────────────────────────────────────────────
        # Rule 2: Check maximum consecutive days
        # ─────────────────────────────────────────────────────────────
        max_consecutive = leave_type.get("max_consecutive_days")
        if max_consecutive and days_requested > max_consecutive:
            errors.append(
                f"Superato limite massimo di {max_consecutive} giorni consecutivi. "
                f"Richiesti: {days_requested} giorni."
            )
        
        # ─────────────────────────────────────────────────────────────
        # Rule 3: Check past dates
        # ─────────────────────────────────────────────────────────────
        if not leave_type.get("allow_past_dates", False):
            today = date.today()
            if start_date < today:
                # Exception for sickness (MAL) - can be retroactive
                if code != "MAL":
                    errors.append(
                        "Non è possibile richiedere assenze per date passate."
                    )
        
        # ─────────────────────────────────────────────────────────────
        # Rule 4: Check overlapping requests
        # ─────────────────────────────────────────────────────────────
        overlapping = await self._request_repo.check_overlap(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            exclude_id=exclude_request_id,
        )
        
        if overlapping:
            dates = [f"{r.start_date} - {r.end_date}" for r in overlapping]
            errors.append(
                f"Esistono già richieste per le date selezionate: {', '.join(dates)}"
            )
        
        # ─────────────────────────────────────────────────────────────
        # Rule 5: Check monthly limit
        # ─────────────────────────────────────────────────────────────
        max_per_month = leave_type.get("max_per_month")
        if max_per_month:
            # Count approved/pending requests in same month
            month_start = start_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_requests = await self._request_repo.get_by_date_range(
                start_date=month_start,
                end_date=month_end,
                user_ids=[user_id],
                status=[LeaveRequestStatus.APPROVED, LeaveRequestStatus.PENDING],
            )
            
            existing_days = sum(
                r.days_requested for r in month_requests
                if r.leave_type_id == leave_type_id and r.id != exclude_request_id
            )
            
            if existing_days + days_requested > max_per_month:
                warnings.append(
                    f"Attenzione: limite mensile di {max_per_month} giorni per {code}. "
                    f"Già utilizzati/richiesti: {existing_days}."
                )
        
        # ─────────────────────────────────────────────────────────────
        # Rule 6: Check balance (if applicable)
        # ─────────────────────────────────────────────────────────────
        balance_sufficient = True
        balance_breakdown = {}
        
        if leave_type.get("scales_balance", False):
            balance_type = leave_type.get("balance_type")
            
            balance = await self._balance_repo.get_by_user_year(
                user_id=user_id,
                year=start_date.year,
            )
            
            if not balance:
                warnings.append("Saldo non trovato per l'anno corrente.")
            else:
                if balance_type == "vacation":
                    available_ap = balance.vacation_available_ap
                    available_ac = balance.vacation_available_ac
                    available_total = available_ap + available_ac
                    
                    if days_requested > available_total:
                        if not leave_type.get("allow_negative_balance", False):
                            balance_sufficient = False
                            errors.append(
                                f"Saldo ferie insufficiente. "
                                f"Disponibile: {available_total} giorni (AP: {available_ap}, AC: {available_ac}). "
                                f"Richiesti: {days_requested} giorni."
                            )
                    
                    # Smart Deduction Check
                    smart_enabled = await self._get_config("smart_deduction_enabled", False)
                    
                    if smart_enabled and available_ap <= 0 and balance.rol_available > 0:
                        # If enabled and no AP vacations, try to suggest ROL? 
                        # Or automatically use ROL? 
                        # For now we just keep FIFO but we logged the check.
                        pass

                    # FIFO: consume AP first, then AC
                    from_ap = min(days_requested, available_ap)
                    from_ac = days_requested - from_ap
                    
                    balance_breakdown = {
                        "vacation_ap": float(from_ap),
                        "vacation_ac": float(from_ac),
                    }
                
                elif balance_type == "rol":
                    available = balance.rol_available
                    hours_requested = days_requested * 8  # Assuming 8h/day
                    
                    if hours_requested > available:
                        if not leave_type.get("allow_negative_balance", False):
                            balance_sufficient = False
                            errors.append(
                                f"Saldo ROL insufficiente. "
                                f"Disponibile: {available} ore. "
                                f"Richieste: {hours_requested} ore."
                            )
                    
                    balance_breakdown = {"rol": float(hours_requested)}
                
                elif balance_type == "permits":
                    available = balance.permits_available
                    hours_requested = days_requested * 8
                    
                    if hours_requested > available:
                        if not leave_type.get("allow_negative_balance", False):
                            balance_sufficient = False
                            errors.append(
                                f"Saldo permessi insufficiente. "
                                f"Disponibile: {available} ore. "
                                f"Richieste: {hours_requested} ore."
                            )
                    
                    balance_breakdown = {"permits": float(hours_requested)}
        
        return PolicyValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            requires_approval=leave_type.get("requires_approval", True),
            balance_sufficient=balance_sufficient,
            balance_breakdown=balance_breakdown,
        )
