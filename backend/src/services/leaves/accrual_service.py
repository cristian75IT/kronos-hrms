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
from src.services.leaves.strategies import StrategyFactory
from src.shared.clients import LeavesWalletClient as WalletClient

class AccrualService:
    """Service for calculating leave accruals and delegating updates to WalletService."""

    def __init__(self, session: AsyncSession, wallet_client: WalletClient):
        self._session = session
        self._wallet_client = wallet_client

    async def recalculate_all_balances(self, year: int):
        """Recalculate accruals for all users based on contracts."""
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        user_ids = result.scalars().all()

        for user_id in user_ids:
            await self.recalculate_user_accrual(user_id, year)

    async def recalculate_user_accrual(self, user_id: UUID, year: int):
        """Recalculate accruals for specific user and year, then sync with WalletService."""
        # 1. Calculate what the balance SHOULD be
        new_vacation, new_rol, new_permits = await self._calculate_accrual_preview(user_id, year)
        
        # 2. Get current wallet to find delta
        wallet = await self._wallet_client.get_wallet(user_id, year)
        if not wallet:
            return
            
        current_vacation = Decimal(str(wallet.get("vacation_accrued", 0)))
        current_rol = Decimal(str(wallet.get("rol_accrued", 0)))
        current_permits = Decimal(str(wallet.get("permits_total", 0)))
        
        # 3. Apply adjustments if any difference
        deltas = {
            "vacation_ac": Decimal(str(new_vacation)) - current_vacation,
            "rol": Decimal(str(new_rol)) - current_rol,
            "permits": Decimal(str(new_permits)) - current_permits
        }
        
        for balance_type, delta in deltas.items():
            if delta == 0:
                continue
            
            payload = {
                "user_id": str(user_id),
                "transaction_type": "adjustment",
                "balance_type": balance_type,
                "amount": float(delta),
                "description": f"Ricalcolo automatico accrual anno {year}",
                "created_by": None # System
            }
            await self._wallet_client.create_transaction(user_id, payload)

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
            # Get confirmed wallet
            wallet = await self._wallet_client.get_wallet(user_id, year)
            current_vacation = float(wallet.get("vacation_accrued", 0)) if wallet else 0
            current_rol = float(wallet.get("rol_accrued", 0)) if wallet else 0
            current_permits = float(wallet.get("permits_total", 0)) if wallet else 0
            
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
                    # Logic matches Strategies logic
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

    async def run_monthly_accruals(self, year: int, month: int):
        """Processes monthly accruals and posts them to WalletService."""
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
                    m_permits = (params["permits"] / 12) * ratio
                    
                    if m_vacation > 0:
                        payload = {
                            "user_id": str(user_id),
                            "transaction_type": "accrual",
                            "balance_type": "vacation_ac",
                            "amount": float(m_vacation),
                            "description": f"Maturazione mensile Ferie {month}/{year}",
                            "expiry_date": date(year + 1, 6, 30).isoformat()
                        }
                        await self._wallet_client.create_transaction(user_id, payload)

                    if m_rol > 0:
                        payload = {
                            "user_id": str(user_id),
                            "transaction_type": "accrual",
                            "balance_type": "rol",
                            "amount": float(m_rol),
                            "description": f"Maturazione mensile ROL {month}/{year}",
                            "expiry_date": date(year + 2, 12, 31).isoformat()
                        }
                        await self._wallet_client.create_transaction(user_id, payload)
                    
                    if m_permits > 0:
                        payload = {
                            "user_id": str(user_id),
                            "transaction_type": "accrual",
                            "balance_type": "permits",
                            "amount": float(m_permits),
                            "description": f"Maturazione mensile Permessi {month}/{year}"
                        }
                        await self._wallet_client.create_transaction(user_id, payload)
                        
                    processed_count += 1
        return processed_count
