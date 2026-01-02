from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal
from typing import Optional, Any, Tuple
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth.models import EmployeeContract, User
from src.services.config.models import NationalContractVersion
from src.services.leaves.repository import LeaveBalanceRepository
from src.services.leaves.strategies import StrategyFactory

class AccrualService:
    """Service for calculating and processing leave accruals."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._balance_repo = LeaveBalanceRepository(session)

    async def recalculate_all_balances(self, year: int):
        """Recalculate accruals for all users based on contracts."""
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        user_ids = result.scalars().all()

        for user_id in user_ids:
            await self.recalculate_user_accrual(user_id, year)

    async def recalculate_user_accrual(self, user_id: UUID, year: int):
        """Recalculate accruals for specific user and year."""
        query = (
            select(EmployeeContract)
            .options(selectinload(EmployeeContract.contract_type))
            .where(EmployeeContract.user_id == user_id)
            .order_by(EmployeeContract.start_date)
        )
        result = await self._session.execute(query)
        contracts = result.scalars().all()

        if not contracts:
            return

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
                    vac_mode = params.get("vacation_mode")
                    rol_mode = params.get("rol_mode")
                    
                    vac_strategy = StrategyFactory.get(vac_mode.function_name if vac_mode else "")
                    rol_strategy = StrategyFactory.get(rol_mode.function_name if rol_mode else "")
                    
                    vac_params = vac_mode.default_parameters.copy() if vac_mode and vac_mode.default_parameters else {}
                    rol_params = rol_mode.default_parameters.copy() if rol_mode and rol_mode.default_parameters else {}
                    
                    if "divisors" in vac_params and isinstance(vac_params["divisors"], dict):
                        vac_params["divisor"] = vac_params["divisors"].get("vacation", 12)
                        
                    if "divisors" in rol_params and isinstance(rol_params["divisors"], dict):
                        rol_params["divisor"] = rol_params["divisors"].get("rol", 12)

                    monthly_vacation = vac_strategy.calculate(
                        params["vacation"], active_contract, month_start, month_end, vac_params
                    )
                    monthly_rol = rol_strategy.calculate(
                        params["rol"], active_contract, month_start, month_end, rol_params
                    )
                    monthly_permits = rol_strategy.calculate(
                        params["permits"], active_contract, month_start, month_end, rol_params
                    )
                    
                    full_time_base = params["full_time_hours"]
                    
                    if active_contract.weekly_hours is not None:
                        ratio = Decimal(active_contract.weekly_hours) / full_time_base
                    else:
                        ratio = Decimal(1.0)
                    
                    if ratio != Decimal(1.0):
                        monthly_vacation *= ratio
                        monthly_rol *= ratio
                        monthly_permits *= ratio
                    
                    total_vacation += monthly_vacation
                    total_rol += monthly_rol
                    total_permits += monthly_permits

        balance = await self._balance_repo.get_or_create(user_id, year)
        
        await self._balance_repo.update(
            balance.id, 
            vacation_accrued=total_vacation,
            rol_accrued=total_rol,
            permits_total=total_permits,
            last_accrual_date=today
        )

    async def _get_monthly_accrual_params(self, contract: EmployeeContract, reference_date: date):
        # 1. Try CCNL config
        if contract.national_contract_id:
            query = (
                select(NationalContractVersion)
                .where(
                    NationalContractVersion.national_contract_id == contract.national_contract_id,
                    NationalContractVersion.valid_from <= reference_date,
                    or_(
                        NationalContractVersion.valid_to >= reference_date,
                        NationalContractVersion.valid_to == None
                    )
                )
                .options(
                selectinload(NationalContractVersion.contract_type_configs),
                selectinload(NationalContractVersion.vacation_calc_mode),
                selectinload(NationalContractVersion.rol_calc_mode)
            )
                .order_by(NationalContractVersion.valid_from.desc())
                .limit(1)
            )
            result = await self._session.execute(query)
            version = result.scalar_one_or_none()
            
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

        # 2. Legacy fallback
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
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        user_ids = result.scalars().all()
        
        for user_id in user_ids:
            balance = await self._balance_repo.get_by_user_year(user_id, year)
            current_vacation = float(balance.vacation_accrued) if balance else 0
            current_rol = float(balance.rol_accrued) if balance else 0
            current_permits = float(balance.permits_total) if balance else 0
            
            new_vacation, new_rol, new_permits = await self._calculate_accrual_preview(user_id, year)
            
            user_query = select(User).where(User.keycloak_id == str(user_id))
            user_result = await self._session.execute(user_query)
            user = user_result.scalar_one_or_none()
            name = f"{user.first_name} {user.last_name}" if user else str(user_id)
            
            previews.append({
                "user_id": user_id,
                "name": name,
                "current_vacation": current_vacation,
                "new_vacation": new_vacation,
                "current_rol": current_rol,
                "new_rol": new_rol,
                "current_permits": current_permits,
                "new_permits": new_permits
            })
        return previews

    async def _calculate_accrual_preview(self, user_id: UUID, year: int) -> Tuple[float, float, float]:
        query = (
            select(EmployeeContract)
            .options(selectinload(EmployeeContract.contract_type))
            .where(EmployeeContract.user_id == user_id)
            .order_by(EmployeeContract.start_date)
        )
        result = await self._session.execute(query)
        contracts = result.scalars().all()

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
                    # Simplified preview logic
                    monthly_vacation = params["vacation"] / 12
                    monthly_rol = params["rol"] / 12
                    monthly_permits = params["permits"] / 12
                    full_time_base = params["full_time_hours"]
                    
                    if active_contract.weekly_hours is not None:
                        ratio = Decimal(active_contract.weekly_hours) / full_time_base
                    else:
                        ratio = Decimal(1.0)
                    
                    if ratio != Decimal(1.0):
                        monthly_vacation *= ratio
                        monthly_rol *= ratio
                        monthly_permits *= ratio
                    
                    total_vacation += monthly_vacation
                    total_rol += monthly_rol
                    total_permits += monthly_permits
        
        return (float(total_vacation), float(total_rol), float(total_permits))

    async def apply_recalculate_selected(self, year: int, user_ids: list[UUID]):
        """Apply recalculation to selected users."""
        for user_id in user_ids:
            await self.recalculate_user_accrual(user_id, year)

    async def run_monthly_accruals(self, year: int, month: int):
        """Processes monthly accruals."""
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        user_ids = result.scalars().all()
        
        accrual_date = date(year, month, 1)
        _, days_in_month = monthrange(year, month)
        month_end = date(year, month, days_in_month)
        
        processed_count = 0
        for user_id in user_ids:
            query = (
                select(EmployeeContract)
                .where(
                    EmployeeContract.user_id == user_id,
                    EmployeeContract.start_date <= month_end,
                    or_(EmployeeContract.end_date >= accrual_date, EmployeeContract.end_date == None)
                )
                .order_by(EmployeeContract.start_date.desc())
            )
            res = await self._session.execute(query)
            contracts = res.scalars().all()
            
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
                    
                    balance = await self._balance_repo.get_or_create(user_id, year)
                    
                    if m_vacation > 0:
                        new_accrued = balance.vacation_accrued + m_vacation
                        await self._balance_repo.update(balance.id, vacation_accrued=new_accrued)
                        await self._balance_repo.add_transaction(
                            balance_id=balance.id,
                            transaction_type="accrual",
                            balance_type="vacation_ac",
                            amount=m_vacation,
                            balance_after=balance.vacation_available_total + m_vacation,
                            reason=f"Maturazione mensile {month}/{year}",
                            expiry_date=date(year + 1, 6, 30)
                        )

                    if m_rol > 0:
                        new_rol = balance.rol_accrued + m_rol
                        await self._balance_repo.update(balance.id, rol_accrued=new_rol)
                        await self._balance_repo.add_transaction(
                            balance_id=balance.id,
                            transaction_type="accrual",
                            balance_type="rol",
                            amount=m_rol,
                            balance_after=balance.rol_available + m_rol,
                            reason=f"Maturazione mensile ROL {month}/{year}",
                            expiry_date=date(year + 2, 12, 31)
                        )
                    processed_count += 1
        return processed_count
