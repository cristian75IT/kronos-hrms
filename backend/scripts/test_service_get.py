import asyncio
import sys
import os

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.config.services import ConfigService

async def test():
    async with get_db_context() as session:
        service = ConfigService(session)
        key = 'approval.auto_escalate'
        value = await service.get(key)
        print(f"Service.get('{key}') returned: {value}")
        
        # Also test repository
        config = await service._config_repo.get_by_key(key)
        if config:
            print(f"Repo.get_by_key('{key}') FOUND: {config.key}")
        else:
            print(f"Repo.get_by_key('{key}') NOT FOUND")

if __name__ == "__main__":
    asyncio.run(test())
