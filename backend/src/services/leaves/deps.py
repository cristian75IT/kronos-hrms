from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload
from src.shared.clients import ConfigClient, LeavesWalletClient as WalletClient
from src.services.leaves.calendar_utils import CalendarUtils

from src.services.leaves.services import LeaveService
from src.services.leaves.balance_service import LeaveBalanceService
from src.services.leaves.accrual_service import AccrualService
from src.services.leaves.calendar_service import LeaveCalendarService
from src.services.leaves.report_service import LeaveReportService

async def get_leave_service(
    session: AsyncSession = Depends(get_db),
) -> LeaveService:
    """Dependency for LeaveService."""
    return LeaveService(session)

async def get_balance_service(
    session: AsyncSession = Depends(get_db),
) -> LeaveBalanceService:
    return LeaveBalanceService(session, WalletClient())

async def get_calendar_service(
    session: AsyncSession = Depends(get_db),
) -> LeaveCalendarService:
    return LeaveCalendarService(session)

async def get_report_service(
    session: AsyncSession = Depends(get_db),
) -> LeaveReportService:
    return LeaveReportService(session, CalendarUtils(ConfigClient()))

async def get_accrual_service(
    session: AsyncSession = Depends(get_db),
) -> AccrualService:
    return AccrualService(session, WalletClient())


async def get_current_user_id(
    token: TokenPayload = Depends(get_current_user),
) -> UUID:
    """Get current user's internal database ID."""
    return token.user_id
