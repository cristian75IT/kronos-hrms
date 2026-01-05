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

    async def get_user(self, user_id: UUID) -> Optional[dict]:
        """Alias for get_user_info for aggregator compatibility."""
        return await self.get_user_info(user_id)

    async def get_users(self, active_only: bool = True) -> list[dict]:
        """Get all users from auth service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/internal/all",
                    params={"active_only": active_only},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"AuthClient error get_users: {e}")
        return []

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

    async def get_employee_trainings(self, user_id: UUID) -> list[dict]:
        """Get safety training records for an employee."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}/trainings",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"AuthClient error get_employee_trainings: {e}")
        return []

    async def get_approvers(self) -> list[dict]:
        """Get all approvers (internal use, no auth required)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/internal/approvers",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"AuthClient get_approvers returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"AuthClient error get_approvers: {e}")
        return []

    async def get_department(self, department_id: UUID) -> Optional[dict]:
        """Get department details including manager_id."""
        try:
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(transport=transport) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/organization/departments/{department_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"AuthClient error get_department: {e}")
        return None

    async def get_service(self, service_id: UUID) -> Optional[dict]:
        """Get service details including coordinator_id."""
        try:
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(transport=transport) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/organization/services/{service_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"AuthClient error get_service: {e}")
        return None


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
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(transport=transport) as client:
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
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(transport=transport) as client:
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
    """Client for Notification Service.
    
    Enterprise-grade notification client with:
    - Multi-channel support (in_app, email)
    - Structured result with delivery status
    - Automatic email resolution
    """
    
    def __init__(self):
        self.base_url = settings.notification_service_url
        self.auth_client = AuthClient()
    
    async def send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        channels: list[str] | None = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
        force_email_lookup: bool = True,
    ) -> dict:
        """Send notification through specified channels.
        
        Args:
            user_id: Target user UUID
            notification_type: Type from NotificationType enum
            title: Notification title
            message: Notification body
            channels: List of channels ["in_app", "email"]. Default: ["in_app", "email"]
            entity_type: Related entity type (e.g., "LeaveRequest")
            entity_id: Related entity ID
            action_url: URL to navigate on click
            force_email_lookup: Whether to fetch user email from auth service
            
        Returns:
            dict with 'success', 'notification_ids', 'email_sent', 'errors'
        """
        if channels is None:
            channels = ["in_app", "email"]
        
        result = {
            "success": False,
            "notification_ids": [],
            "email_sent": False,
            "errors": [],
        }
        
        try:
            user_email = None
            if force_email_lookup:
                user_email = await self.auth_client.get_user_email(user_id)
                if not user_email:
                    logger.warning(f"Notification skipped: No email for user {user_id}")
                    result["errors"].append(f"No email found for user {user_id}")
                    return result

            # Send to each channel
            for channel in channels:
                try:
                    payload = {
                        "user_id": str(user_id),
                        "user_email": user_email,
                        "notification_type": notification_type,
                        "title": title,
                        "message": message,
                        "channel": channel,
                        "entity_type": entity_type,
                        "entity_id": str(entity_id) if entity_id else None,
                        "action_url": action_url,
                    }
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{self.base_url}/api/v1/notifications",
                            json=payload,
                            timeout=10.0
                        )
                        
                        if response.status_code == 201:
                            data = response.json()
                            result["notification_ids"].append(data.get("id"))
                            if channel == "email":
                                result["email_sent"] = True
                        else:
                            result["errors"].append(f"{channel}: {response.status_code}")
                            
                except Exception as e:
                    logger.error(f"NotificationClient error ({channel}): {e}")
                    result["errors"].append(f"{channel}: {str(e)}")
            
            result["success"] = len(result["notification_ids"]) > 0
            
        except Exception as e:
            logger.error(f"NotificationClient error: {e}")
            result["errors"].append(str(e))
        
        return result
    
    async def send_with_email(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> dict:
        """Convenience method: send both in_app and email notification."""
        return await self.send_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            channels=["in_app", "email"],
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
        )

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
            
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(transport=transport) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves-wallets/internal/wallets/{user_id}",
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
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(transport=transport) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves-wallets/internal/wallets/{user_id}/summary",
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
                
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(transport=transport) as client:
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
                    f"{self.base_url}/api/v1/leaves-wallets/internal/transactions",
                    json=data,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"LeavesWalletClient error create_transaction: {response.status_code} - {response.text}")
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
    """
    Client for Trip Wallet Service (Trasferte).
    
    Enterprise-grade client with:
    - Wallet queries and summaries
    - Budget reservation system
    - Policy limit checking
    - Reconciliation and settlement
    """
    
    def __init__(self):
        self.base_url = settings.expensive_wallet_service_url
        
    async def get_status(self, trip_id: UUID) -> Optional[dict]:
        """Get wallet status for a trip."""
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

    async def get_wallet_summary(self, trip_id: UUID) -> Optional[dict]:
        """Get comprehensive wallet summary."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expensive-wallets/{trip_id}/summary",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error get_wallet_summary: {e}")
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
        """Initialize wallet for a trip (internal system call)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/internal/initialize/{trip_id}",
                    params={"user_id": str(user_id), "budget": budget},
                    timeout=5.0
                )
                if response.status_code in (200, 201):
                    return response.json()
                logger.warning(f"ExpensiveWalletClient initialize_wallet {trip_id} returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error initialize_wallet: {e}")
        return None

    async def get_transactions(self, trip_id: UUID, limit: int = 100) -> list:
        """Get expense wallet transactions for a trip."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expensive-wallets/{trip_id}/transactions",
                    params={"limit": limit},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"ExpensiveWalletClient get_transactions {trip_id} returned {response.status_code}")
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error get_transactions: {e}")
        return []

    # ═══════════════════════════════════════════════════════════
    # Budget Reservation (Internal API)
    # ═══════════════════════════════════════════════════════════

    async def check_budget_available(self, trip_id: UUID, amount: float) -> tuple[bool, float]:
        """Check if budget is available for an expense."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expensive-wallets/internal/{trip_id}/check-budget",
                    params={"amount": amount},
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return (data.get("available", False), data.get("available_amount", 0))
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error check_budget_available: {e}")
        return (False, 0.0)

    async def reserve_budget(
        self,
        trip_id: UUID,
        amount: float,
        reference_id: UUID,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        """Reserve budget for a pending expense."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/internal/{trip_id}/reserve",
                    json={
                        "amount": amount,
                        "reference_id": str(reference_id),
                        "category": category,
                        "description": description,
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error reserve_budget: {e}")
        return None

    async def confirm_expense(self, trip_id: UUID, reference_id: UUID) -> bool:
        """Confirm a reserved expense."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/internal/{trip_id}/confirm/{reference_id}",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error confirm_expense: {e}")
        return False

    async def cancel_expense(self, trip_id: UUID, reference_id: UUID) -> bool:
        """Cancel a reserved expense."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/internal/{trip_id}/cancel/{reference_id}",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error cancel_expense: {e}")
        return False

    async def check_policy_limit(
        self,
        trip_id: UUID,
        category: str,
        amount: float,
    ) -> dict:
        """Check if expense exceeds policy limits."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/internal/{trip_id}/check-policy",
                    json={"category": category, "amount": amount},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error check_policy_limit: {e}")
        return {"allowed": True, "requires_approval": False}

    # ═══════════════════════════════════════════════════════════
    # Admin Operations
    # ═══════════════════════════════════════════════════════════

    async def reconcile_wallet(
        self,
        trip_id: UUID,
        notes: Optional[str] = None,
        adjustments: Optional[list] = None,
    ) -> Optional[dict]:
        """Reconcile a trip wallet."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/admin/{trip_id}/reconcile",
                    json={"notes": notes, "adjustments": adjustments or []},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error reconcile_wallet: {e}")
        return None

    async def settle_wallet(
        self,
        trip_id: UUID,
        payment_reference: Optional[str] = None,
    ) -> Optional[dict]:
        """Final settlement of a trip wallet."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/admin/{trip_id}/settle",
                    json={"payment_reference": payment_reference},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error settle_wallet: {e}")
        return None

    async def update_budget(
        self,
        trip_id: UUID,
        new_budget: float,
        reason: str,
    ) -> Optional[dict]:
        """Update trip budget."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/expensive-wallets/admin/{trip_id}/update-budget",
                    json={"new_budget": new_budget, "reason": reason},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpensiveWalletClient error update_budget: {e}")
        return None


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
                # Use the new endpoint in calendar router (we need to add it first!)
                # For now, I will assume I will add GET /api/v1/calendar/holidays
                response = await client.get(
                    f"{self.base_url}/api/v1/calendar/holidays-list",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
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
                    f"{self.base_url}/api/v1/calendar/closures-list",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
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

    async def get_working_days_count(self, start_date: date, end_date: date) -> int:
        """Wrapper for calculating working days count used by aggregator."""
        res = await self.calculate_working_days(start_date, end_date)
        if res:
            return int(res.get("working_days", 0))
        return 0


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

    async def get_pending_requests_count(self) -> int:
        """Get count of pending leave requests."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves/internal/pending-count",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return int(response.json())
        except Exception as e:
            logger.error(f"LeavesClient error get_pending_requests_count: {e}")
        return 0

    async def get_all_requests(
        self, 
        user_id: Optional[UUID] = None,
        year: Optional[int] = None,
        status: Optional[str] = None
    ) -> list[dict]:
        """Get leave requests with filters."""
        try:
            params = {}
            if user_id:
                params["user_id"] = str(user_id)
            if year:
                params["year"] = year
            if status:
                params["status"] = status
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves/history",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"LeavesClient error get_all_requests: {e}")
        return []

    async def get_leaves_in_period(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> list[dict]:
        """Get leaves in period (internal use)."""
        try:
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
            if user_id:
                params["user_id"] = str(user_id)
            if status:
                params["status"] = status
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/leaves/internal/requests",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"LeavesClient get_leaves_in_period returned {response.status_code}")
        except Exception as e:
            logger.error(f"LeavesClient error get_leaves_in_period: {e}")
        return []

    async def get_leaves_for_date(self, target_date: date) -> list[dict]:
        """Get leaves for a specific date (internal)."""
        return await self.get_leaves_in_period(target_date, target_date, status="approved,approved_conditional")


# Alias for compatibility with HR Reporting service
LeavesClient = LeaveClient


class ExpenseClient:
    """
    Client for Expense Service interactions.
    
    Used by HR Reporting service for aggregating expense data.
    """
    
    def __init__(self):
        self.base_url = settings.expense_service_url if hasattr(settings, 'expense_service_url') else "http://localhost:8010"
    
    async def get_pending_reports_count(self) -> int:
        """Get count of pending expense reports."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expenses/pending",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return len(data) if isinstance(data, list) else 0
        except Exception as e:
            logger.error(f"ExpenseClient error get_pending_reports_count: {e}")
        return 0
    
    async def get_pending_trips_count(self) -> int:
        """Get count of pending trip requests."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/trips/pending",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return len(data) if isinstance(data, list) else 0
        except Exception as e:
            logger.error(f"ExpenseClient error get_pending_trips_count: {e}")
        return 0
    
    async def get_user_trips(self, user_id: UUID, year: Optional[int] = None) -> list:
        """Get trips for a user."""
        try:
            params = {}
            if year:
                params["year"] = year
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expenses/trips",
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpenseClient error get_user_trips: {e}")
        return []
    
    async def get_user_expense_reports(self, user_id: UUID, year: Optional[int] = None) -> list:
        """Get expense reports for a user."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expenses/reports/my",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpenseClient error get_user_expense_reports: {e}")
        return []

    async def get_trips_for_date(self, target_date: date) -> list[dict]:
        """Get all active trips for a specific date across all users."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/expenses/internal/trips-for-date",
                    params={"target_date": target_date.isoformat()},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ExpenseClient error get_trips_for_date: {e}")
        return []


class ApprovalClient:
    """Client for Approval Service interactions."""
    
    def __init__(self):
        self.base_url = getattr(settings, 'approval_service_url', 'http://approval-service:8012')
    
    async def create_request(
        self,
        entity_type: str,
        entity_id: UUID,
        requester_id: UUID,
        title: str,
        entity_ref: Optional[str] = None,
        requester_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        callback_url: Optional[str] = None,
        approver_ids: Optional[list[UUID]] = None,
    ) -> Optional[dict]:
        """Create an approval request."""
        try:
            payload = {
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "entity_ref": entity_ref,
                "requester_id": str(requester_id),
                "requester_name": requester_name,
                "title": title,
                "description": description,
                "metadata": metadata or {},
                "callback_url": callback_url,
            }
            
            if approver_ids:
                payload["approver_ids"] = [str(a) for a in approver_ids]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/approvals/internal/request",
                    json=payload,
                    timeout=10.0
                )
                if response.status_code in (200, 201):
                    return response.json()
                else:
                    logger.error(f"ApprovalClient create_request failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"ApprovalClient error create_request: {e}")
        return None
    
    async def check_status(self, entity_type: str, entity_id: UUID) -> Optional[dict]:
        """Check approval status for an entity."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/approvals/internal/status/{entity_type}/{entity_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ApprovalClient error check_status: {e}")
        return None
    
    async def get_pending_count(self, user_id: UUID) -> dict:
        """Get pending approval count for a user."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/approvals/decisions/pending/count",
                    headers={"X-User-Id": str(user_id)},  # Would need proper auth
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ApprovalClient error get_pending_count: {e}")
        return {"total": 0, "urgent": 0, "by_type": {}}
    
    async def cancel_request(self, entity_type: str, entity_id: UUID, reason: Optional[str] = None) -> bool:
        """Cancel an approval request by entity."""
        try:
            # First get the request
            status = await self.check_status(entity_type, entity_id)
            if not status or not status.get("approval_request_id"):
                return False
            
            request_id = status["approval_request_id"]
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/approvals/requests/{request_id}",
                    json={"reason": reason} if reason else None,
                    timeout=5.0
                )
                return response.status_code == 204
        except Exception as e:
            logger.error(f"ApprovalClient error cancel_request: {e}")
        return False

    async def get_by_entity(self, entity_type: str, entity_id: UUID) -> Optional[dict]:
        """Get approval request by entity type and ID."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/approvals/internal/by-entity/{entity_type}/{entity_id}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"ApprovalClient get_by_entity returned {response.status_code}")
        except Exception as e:
            logger.error(f"ApprovalClient error get_by_entity: {e}")
        return None

    async def approve(
        self, 
        approval_request_id: UUID, 
        approver_id: UUID, 
        notes: Optional[str] = None
    ) -> Optional[dict]:
        """Approve an approval request."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/approvals/internal/approve/{approval_request_id}",
                    json={
                        "approver_id": str(approver_id),
                        "notes": notes,
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"ApprovalClient approve failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"ApprovalClient error approve: {e}")
        return None

    async def reject(
        self, 
        approval_request_id: UUID, 
        approver_id: UUID, 
        notes: str
    ) -> Optional[dict]:
        """Reject an approval request."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/approvals/internal/reject/{approval_request_id}",
                    json={
                        "approver_id": str(approver_id),
                        "notes": notes,
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"ApprovalClient reject failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"ApprovalClient error reject: {e}")
        return None

