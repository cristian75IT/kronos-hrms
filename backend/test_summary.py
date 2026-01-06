
import asyncio
from uuid import UUID
from src.services.leaves.services import LeaveService
from src.core.database import async_session_factory
from pydantic import RootModel

async def test():
    async with async_session_factory() as session:
        service = LeaveService(session)
        # Test with a dummy UUID or a known one from logs
        user_id = UUID('5d6d1838-26a6-4bed-a0cf-cdcd15e99a27')
        try:
            summary = await service.get_balance_summary(user_id, 2025)
            print(summary.model_dump_json(indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
