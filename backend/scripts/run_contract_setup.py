import asyncio
import sys
import os
import json
from pathlib import Path

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.config.services import ConfigService
from src.services.config.schemas import SetupContractsPayload
from src.services.config.routers.setup import setup_contracts

async def run_setup():
    print("🚀 Running Contract Setup...")
    # Load data
    setup_data_path = Path(__file__).parent.parent / "setup_data" / "contracts.json"
    if not setup_data_path.exists():
        print(f"❌ Setup data not found: {setup_data_path}")
        return

    with open(setup_data_path, "r") as f:
        data = json.load(f)
    
    payload = SetupContractsPayload(**data)
    
    async with get_db_context() as session:
        service = ConfigService(session)
        # Mock token/actor for audit logic
        from src.core.security import TokenPayload
        from uuid import UUID
        token = TokenPayload(
            sub="456255c9-3f01-42c1-87b6-1f9240b4087b", # Keycloak ID
            internal_user_id=UUID("3a5b855c-e426-42e0-a51a-210fc1ac3f61"),
            preferred_username="admin",
            email="cristian@example.com",
            realm_access={"roles": ["admin"]}
        )
        
        results = await setup_contracts(payload=payload, token=token, service=service)
        print(f"✨ Results: {results}")

if __name__ == "__main__":
    asyncio.run(run_setup())
