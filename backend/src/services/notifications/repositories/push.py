from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.notifications.models import PushSubscription

class PushSubscriptionRepository:
    """Repository for Web Push subscriptions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[PushSubscription]:
        """Get subscription by ID."""
        result = await self._session.execute(
            select(PushSubscription).where(PushSubscription.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[PushSubscription]:
        """Get all active subscriptions for a user."""
        result = await self._session.execute(
            select(PushSubscription)
            .where(
                and_(
                    PushSubscription.user_id == user_id,
                    PushSubscription.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    async def get_by_endpoint(self, endpoint: str) -> Optional[PushSubscription]:
        """Get subscription by endpoint URL."""
        result = await self._session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: UUID,
        endpoint: str,
        p256dh: str,
        auth: str,
        device_info: Optional[dict] = None,
    ) -> PushSubscription:
        """Create or update subscription."""
        # Check if subscription already exists for this endpoint
        existing = await self.get_by_endpoint(endpoint)
        if existing:
            existing.user_id = user_id
            existing.p256dh = p256dh
            existing.auth = auth
            existing.device_info = device_info
            existing.is_active = True
            await self._session.flush()
            return existing
        
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            device_info=device_info,
        )
        self._session.add(subscription)
        await self._session.flush()
        return subscription

    async def deactivate(self, id: UUID) -> bool:
        """Deactivate a subscription."""
        subscription = await self.get(id)
        if not subscription:
            return False
        subscription.is_active = False
        await self._session.flush()
        return True

    async def delete_by_endpoint(self, endpoint: str) -> bool:
        """Delete subscription by endpoint."""
        result = await self._session.execute(
            delete(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        return result.rowcount > 0

    async def delete_by_user(self, user_id: UUID) -> int:
        """Delete all subscriptions for a user."""
        result = await self._session.execute(
            delete(PushSubscription).where(PushSubscription.user_id == user_id)
        )
        return result.rowcount
