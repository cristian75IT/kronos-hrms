import logging
from datetime import date
from typing import Optional, Any
from uuid import UUID

import httpx
from pydantic import BaseModel

from src.core.config import settings

logger = logging.getLogger(__name__)


class AuthClient:
    """Client for Auth Service interactions."""
    
    def __init__(self):
        self.base_url = settings.auth_service_url
        
    async def get_user_info(self, user_id: UUID) -> Optional[dict]:
        """Get user details from auth service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"AuthClient error get_user_info: {e}")
        return None

    async def get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email."""
        user = await self.get_user_info(user_id)
        return user.get("email") if user else None

    async def get_subordinates(self, manager_id: UUID) -> list[UUID]:
        """Get subordinates for a manager."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/subordinates/{manager_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    # Expecting list of dicts with 'id'
                    return [UUID(u["id"]) for u in data if u.get("id")]
        except Exception as e:
            logger.error(f"AuthClient error get_subordinates: {e}")
        return []


class ConfigClient:
    """Client for Config Service interactions."""
    
    def __init__(self):
        self.base_url = settings.config_service_url

    async def get_holidays(
        self, 
        year: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> list[dict]:
        """[DEPRECATED] Get holidays. Use CalendarClient.get_holidays() instead."""
        try:
            params = {"year": year}
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/holidays",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                         return data.get("items", [])
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"ConfigClient error get_holidays: {e}")
        return []

    async def get_company_closures(self, year: int) -> list[dict]:
        """[DEPRECATED] Get company closures. Use CalendarClient.get_closures() instead."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/closures",
                    params={"year": year},
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", []) if isinstance(data, dict) else []
        except Exception as e:
            logger.error(f"ConfigClient error get_company_closures: {e}")
        return []

    async def get_expense_types(self) -> list[dict]:
        """Get all expense types."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expense-types",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ConfigClient error get_expense_types: {e}")
        return []
        
    async def get_sys_config(self, key: str, default: Any = None) -> Any:
        """Get system config value."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/config/{key}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("value", default)
        except Exception as e:
            logger.error(f"ConfigClient error get_sys_config: {e}")
        return default

    async def get_leave_type(self, leave_type_id: UUID) -> Optional[dict]:
        """Get leave type details."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leave-types/{leave_type_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
             logger.error(f"ConfigClient error get_leave_type: {e}")
        return None


class NotificationClient:
    """Client for Notification Service."""
    
    def __init__(self):
        self.base_url = settings.notification_service_url
        self.auth_client = AuthClient()
    
    async def send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        force_email_lookup: bool = True
    ) -> None:
        """Send notification. Resolves email automatically."""
        try:
            user_email = None
            if force_email_lookup:
                user_email = await self.auth_client.get_user_email(user_id)
                if not user_email:
                    logger.warning(f"Notification skipped: No email for user {user_id}")
                    return

            payload = {
                "user_id": str(user_id),
                "user_email": user_email,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "channel": "in_app", # Default, ideally configurable
                "entity_type": entity_type,
                "entity_id": str(entity_id) if entity_id else None,
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/api/v1/notifications",
                    json=payload,
                    timeout=5.0
                )
        except Exception as e:
             logger.error(f"NotificationClient error: {e}")

class LeavesWalletClient:
    """
    Client for Leaves Wallet Service (Ferie, ROL, Permessi).
    
    Enterprise-grade client with:
    - Balance queries
    - Reservation system integration
    - Transaction processing
    """
    
    def __init__(self):
        self.base_url = settings.leaves_wallet_service_url
        
    async def get_wallet(self, user_id: UUID, year: int = None) -> Optional[dict]:
        """Get user leaves wallet."""
        try:
            params = {}
            if year:
                params["year"] = year
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves-wallets/{user_id}",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"LeavesWalletClient error get_wallet: {e}")
        return None

    async def get_balance_summary(self, user_id: UUID, year: int = None) -> Optional[dict]:
        """Get comprehensive balance summary."""
        try:
            params = {"year": year} if year else {}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves-wallets/{user_id}/summary",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"LeavesWalletClient error get_balance_summary: {e}")
        return None

    async def get_available_balance(
        self, 
        user_id: UUID, 
        balance_type: str,
        year: int = None,
        exclude_reserved: bool = True,
    ) -> Optional[float]:
        """Get available balance for a specific type."""
        try:
            params = {"exclude_reserved": exclude_reserved}
            if year:
                params["year"] = year
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves-wallets/{user_id}/available/{balance_type}",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json().get("available")
        except Exception as e:
            logger.error(f"LeavesWalletClient error get_available_balance: {e}")
        return None

    async def check_balance_sufficient(
        self,
        user_id: UUID,
        balance_type: str,
        amount: float,
        year: int = None,
    ) -> tuple[bool, float]:
        """Check if balance is sufficient for a request."""
        try:
            params = {
                "user_id": str(user_id),
                "balance_type": balance_type,
                "amount": amount,
            }
            if year:
                params["year"] = year
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves-wallets/internal/check",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return (data.get("sufficient", False), data.get("available", 0))
        except Exception as e:
            logger.error(f"LeavesWalletClient error check_balance_sufficient: {e}")
        return (False, 0.0)

    async def create_transaction(self, user_id: UUID, data: dict) -> Optional[dict]:
        """Create a wallet transaction."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/leaves-wallets/{user_id}/transactions",
                    json=data,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"LeavesWalletClient error create_transaction: {e}")
        return None

    async def reserve_balance(
        self,
        user_id: UUID,
        balance_type: str,
        amount: float,
        reference_id: UUID,
        expiry_date: Optional[date] = None,
    ) -> Optional[dict]:
        """Reserve balance for a pending request."""
        try:
            params = {
                "user_id": str(user_id),
                "balance_type": balance_type,
                "amount": amount,
                "reference_id": str(reference_id),
            }
            if expiry_date:
                params["expiry_date"] = expiry_date.isoformat()
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/leaves-wallets/internal/reserve",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"LeavesWalletClient error reserve_balance: {e}")
        return None

    async def confirm_reservation(self, reference_id: UUID) -> bool:
        """Confirm a reservation when request is approved."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/leaves-wallets/internal/confirm/{reference_id}",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LeavesWalletClient error confirm_reservation: {e}")
        return False

    async def cancel_reservation(self, reference_id: UUID) -> bool:
        """Cancel a reservation when request is rejected."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/leaves-wallets/internal/cancel/{reference_id}",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LeavesWalletClient error cancel_reservation: {e}")
        return False

    async def get_transactions(self, identifier: UUID, limit: int = 100) -> list:
        """Get wallet transactions by wallet_id."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves-wallets/transactions/{identifier}",
                    params={"limit": limit},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"LeavesWalletClient error get_transactions: {e}")
        return []

class ExpensiveWalletClient:
    """Client for NEW Trips Expense Wallet Service (Trasferte)."""
    
    def __init__(self):
        self.base_url = settings.expensive_wallet_service_url
        
    async def get_status(self, trip_id: UUID) -> Optional[dict]:
        """Get expensive wallet status for a trip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expensive-wallets/{trip_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"ExpensiveWalletClient get_status {trip_id} returned {response.status_code}")
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error get_status: {e}")
        return None

    async def create_transaction(self, trip_id: UUID, data: dict) -> Optional[dict]:
        """Create a travel wallet transaction (advance, expense, refund)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/{trip_id}/transactions",
                    json=data,
                    timeout=5.0
                )
                if response.status_code == 201:
                    return response.json()
                logger.warning(f"ExpensiveWalletClient create_transaction {trip_id} returned {response.status_code}")
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error create_transaction: {e}")
        return None

    async def initialize_wallet(self, trip_id: UUID, user_id: UUID, budget: float) -> Optional[dict]:
        """Initialize wallet for a trip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/initialize/{trip_id}",
                    params={"user_id": str(user_id), "budget": budget},
                    timeout=5.0
                )
                if response.status_code in (200, 201):
                    return response.json()
                logger.warning(f"ExpensiveWalletClient initialize_wallet {trip_id} returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error initialize_wallet: {e}")
        return None

    async def get_transactions(self, trip_id: UUID) -> list:
        """Get expense wallet transactions for a trip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expensive-wallets/{trip_id}/transactions",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"ExpensiveWalletClient get_transactions {trip_id} returned {response.status_code}")
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error get_transactions: {e}")
        return []


class CalendarClient:
    """Client for Calendar Service interactions."""
    
    def __init__(self):
        self.base_url = settings.calendar_service_url if hasattr(settings, 'calendar_service_url') else "http://calendar-service:8009"

    async def get_holidays(
        self, 
        year: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> list[dict]:
        """Get holidays from calendar service."""
        try:
            params = {"year": year}
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/holidays",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else data.get("items", [])
        except Exception as e:
            logger.error(f"CalendarClient error get_holidays: {e}")
        return []

    async def get_closures(self, year: int, location_id: Optional[UUID] = None) -> list[dict]:
        """Get company closures from calendar service."""
        try:
            params = {"year": year}
            if location_id:
                params["location_id"] = str(location_id)
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/closures",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else data.get("items", [])
        except Exception as e:
            logger.error(f"CalendarClient error get_closures: {e}")
        return []

    async def get_calendar_range(
        self, 
        start_date: date, 
        end_date: date,
        location_id: Optional[UUID] = None
    ) -> Optional[dict]:
        """Get aggregated calendar view for a date range."""
        try:
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
            if location_id:
                params["location_id"] = str(location_id)
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/calendar/range",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"CalendarClient error get_calendar_range: {e}")
        return None

    async def calculate_working_days(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        exclude_closures: bool = True,
        exclude_holidays: bool = True,
    ) -> Optional[dict]:
        """Calculate working days between two dates."""
        try:
            payload = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "exclude_closures": exclude_closures,
                "exclude_holidays": exclude_holidays,
            }
            if location_id:
                payload["location_id"] = str(location_id)
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/calendar/working-days",
                    json=payload,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"CalendarClient error calculate_working_days: {e}")
        return None

    async def is_working_day(
        self,
        check_date: date,
        location_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a specific date is a working day."""
        try:
            params = {}
            if location_id:
                params["location_id"] = str(location_id)
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/calendar/working-days/check/{check_date.isoformat()}",
                    params=params if params else None,
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("is_working_day", True)
        except Exception as e:
            logger.error(f"CalendarClient error is_working_day: {e}")
        return True  # Default to working day on error


class LeaveClient:
    """Client for Leave Service interactions (for inter-service communication)."""
    
    def __init__(self):
        self.base_url = settings.leave_service_url
    
    async def recalculate_for_closure(self, closure_start: date, closure_end: date) -> Optional[dict]:
        """
        Trigger recalculation of leave requests that overlap with a closure.
        
        Called by calendar service when a company closure is created or modified.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/internal/recalculate-for-closure",
                    params={
                        "closure_start": closure_start.isoformat(),
                        "closure_end": closure_end.isoformat(),
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"LeaveClient recalculate_for_closure returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"LeaveClient error recalculate_for_closure: {e}")
        return None
