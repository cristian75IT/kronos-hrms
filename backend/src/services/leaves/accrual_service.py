"""
KRONOS - Accrual Service

Calculates leave accruals and syncs with Enterprise Time Ledger.
Legacy Wallet integration removed.
"""
from datetime import date
from calendar import monthrange
from decimal import Decimal
from typing import Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.leaves.repository import ContractRepository
from src.services.leaves.ledger import TimeLedgerService, TimeLedgerBalanceType


class AccrualService:
    """Service for calculating leave accruals via TimeLedgerService."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._contract_repo = ContractRepository(session)
        self._ledger_service = TimeLedgerService(session)

    async def recalculate_all_balances(self, year: int):
        """Recalculate accruals for all users based on contracts."""
        user_ids = await self._contract_repo.get_distinct_user_ids()

        for user_id in user_ids:
            await self.recalculate_user_accrual(user_id, year)

    async def recalculate_user_accrual(self, user_id: UUID, year: int):
        """Recalculate accruals for specific user and year."""
        # Calculate what SHOULD be there
        new_vacation, new_rol, new_permits = await self._calculate_accrual_preview(user_id, year)
        
        # Get what IS there
        summary = await self._ledger_service.get_balance_summary(user_id, year)
        
        current_vacation = summary.vacation_ac.total_credited
        current_rol = summary.rol.total_credited
        current_permits = summary.permits.total_credited
        
        deltas = {
            TimeLedgerBalanceType.VACATION_AC: Decimal(str(new_vacation)) - current_vacation,
            TimeLedgerBalanceType.ROL: Decimal(str(new_rol)) - current_rol,
            TimeLedgerBalanceType.PERMITS: Decimal(str(new_permits)) - current_permits
        }
        
        from src.services.leaves.ledger.repository import TimeLedgerRepository
        from src.services.leaves.ledger.models import TimeLedgerEntry, TimeLedgerEntryType
        repo = TimeLedgerRepository(self._session)

        for balance_type, delta in deltas.items():
            if delta == 0:
                continue
            
            entry_type = TimeLedgerEntryType.ADJUSTMENT_ADD if delta > 0 else TimeLedgerEntryType.ADJUSTMENT_SUB
            
            # Record adjustment directly
            entry = TimeLedgerEntry(
                user_id=user_id,
                year=year,
                entry_type=entry_type,
                balance_type=balance_type,
                amount=abs(delta),
                reference_type="ACCRUAL_RECALCULATION",
                reference_id=uuid4(),
                reference_status="COMPLETED",
                notes=f"Ricalcolo automatico accrual anno {year}"
            )
            await repo.create(entry)

    async def _get_monthly_accrual_params(self, contract, reference_date: date):
        """Get accrual parameters for a contract."""
        if contract.national_contract_id:
            version = await self._contract_repo.get_national_contract_version(
                contract.national_contract_id, reference_date
            )
            
            if version:
                type_config = next(
                    (c for c in version.contract_type_configs if c.contract_type_id == contract.contract_type_id),
                    None
                )
                
                if type_config:
                    return {
                        "vacation": Decimal(type_config.annual_vacation_days),
                        "rol": Decimal(type_config.annual_rol_hours),
                        "permits": Decimal(type_config.annual_ex_festivita_hours),
                        "full_time_hours": Decimal(type_config.weekly_hours if type_config.weekly_hours > 0 else version.weekly_hours_full_time),
                        "vacation_mode": version.vacation_calc_mode,
                        "rol_mode": version.rol_calc_mode
                    }
                
                return {
                    "vacation": Decimal(version.annual_vacation_days),
                    "rol": Decimal(version.annual_rol_hours),
                    "permits": Decimal(version.annual_ex_festivita_hours),
                    "full_time_hours": Decimal(version.weekly_hours_full_time),
                    "vacation_mode": version.vacation_calc_mode,
                    "rol_mode": version.rol_calc_mode
                }

        if contract.contract_type:
            ctype = contract.contract_type
            return {
                "vacation": Decimal(ctype.annual_vacation_days),
                "rol": Decimal(ctype.annual_rol_hours),
                "permits": Decimal(ctype.annual_permit_hours),
                "full_time_hours": Decimal(40.0)
            }
            
        return None

    async def preview_recalculate(self, year: int) -> list[dict]:
        """Preview recalculation changes."""
        previews = []
        user_ids = await self._contract_repo.get_distinct_user_ids()
        
        for user_id in user_ids:
            summary = await self._ledger_service.get_balance_summary(user_id, year)
            
            current_vacation = float(summary.vacation_ac.total_credited)
            current_rol = float(summary.rol.total_credited)
            current_permits = float(summary.permits.total_credited)
            
            new_vacation, new_rol, new_permits = await self._calculate_accrual_preview(user_id, year)
            
            previews.append({
                "user_id": str(user_id),
                "current_vacation": current_vacation,
                "new_vacation": new_vacation,
                "current_rol": current_rol,
                "new_rol": new_rol,
                "current_permits": current_permits,
                "new_permits": new_permits
            })
        return previews

    async def _calculate_accrual_preview(self, user_id: UUID, year: int) -> Tuple[float, float, float]:
        """Calculate expected accruals for preview."""
        contracts = await self._contract_repo.get_user_contracts(user_id)

        if not contracts:
            return (0, 0, 0)

        total_vacation = Decimal(0)
        total_rol = Decimal(0)
        total_permits = Decimal(0)
        
        today = date.today()
        
        for month in range(1, 13):
            month_start = date(year, month, 1)
            _, last_day = monthrange(year, month)
            month_end = date(year, month, last_day)
            
            if month_start > today:
                break
                
            active_contract = None
            for contract in contracts:
                c_start = contract.start_date
                c_end = contract.end_date or date(9999, 12, 31)
                
                if c_start <= month_end and c_end >= month_start:
                    active_contract = contract
                    if c_start <= month_start:
                        break
            
            if active_contract:
                params = await self._get_monthly_accrual_params(active_contract, month_start)
                
                if params:
                    ratio = Decimal(active_contract.weekly_hours or params["full_time_hours"]) / params["full_time_hours"]
                    
                    monthly_vacation = (params["vacation"] / 12) * ratio
                    monthly_rol = (params["rol"] / 12) * ratio
                    monthly_permits = (params["permits"] / 12) * ratio
                    
                    total_vacation += monthly_vacation
                    total_rol += monthly_rol
                    total_permits += monthly_permits
        
        return (float(total_vacation), float(total_rol), float(total_permits))

    async def apply_recalculate_selected(self, year: int, user_ids: list[UUID]):
        """Apply recalculation to selected users."""
        for user_id in user_ids:
            await self.recalculate_user_accrual(user_id, year)

    async def run_monthly_accruals(self, year: int, month: int) -> int:
        """Processes monthly accruals."""
        user_ids = await self._contract_repo.get_distinct_user_ids()
        
        accrual_date = date(year, month, 1)
        _, days_in_month = monthrange(year, month)
        month_end = date(year, month, days_in_month)
        
        job_id = uuid4() # Generate a job ID for this run
        
        processed_count = 0
        for user_id in user_ids:
            contracts = await self._contract_repo.get_contracts_in_month(user_id, accrual_date, month_end)
            
            if not contracts:
                continue
                
            active_contract = None
            for contract in contracts:
                overlap_start = max(contract.start_date, accrual_date)
                overlap_end = min(contract.end_date or date(9999, 12, 31), month_end)
                overlap_days = (overlap_end - overlap_start).days + 1
                
                if overlap_days >= 15:
                    active_contract = contract
                    break
            
            if active_contract:
                params = await self._get_monthly_accrual_params(active_contract, accrual_date)
                if params:
                    full_time_base = params["full_time_hours"]
                    ratio = Decimal(active_contract.weekly_hours or full_time_base) / full_time_base
                    
                    m_vacation = (params["vacation"] / 12) * ratio
                    m_rol = (params["rol"] / 12) * ratio
                    m_permits = (params["permits"] / 12) * ratio
                    
                    if m_vacation > 0:
                        await self._ledger_service.record_accrual(
                            user_id=user_id,
                            balance_type=TimeLedgerBalanceType.VACATION_AC,
                            amount=m_vacation,
                            year=year,
                            job_id=job_id,
                            notes=f"Maturazione mensile Ferie {month}/{year}"
                        )

                    if m_rol > 0:
                        await self._ledger_service.record_accrual(
                            user_id=user_id,
                            balance_type=TimeLedgerBalanceType.ROL,
                            amount=m_rol,
                            year=year,
                            job_id=job_id,
                            notes=f"Maturazione mensile ROL {month}/{year}"
                        )
                    
                    if m_permits > 0:
                        await self._ledger_service.record_accrual(
                            user_id=user_id,
                            balance_type=TimeLedgerBalanceType.PERMITS,
                            amount=m_permits,
                            year=year,
                            job_id=job_id,
                            notes=f"Maturazione mensile Permessi {month}/{year}"
                        )
                        
                    processed_count += 1
        return processed_count
