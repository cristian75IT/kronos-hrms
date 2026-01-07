
import asyncio
from src.shared.clients import ConfigClient

async def check():
    client = ConfigClient()
    try:
        block = await client.get_sys_config('leaves.block_insufficient_balance', True)
        print(f"block_insufficient_balance: {block}")
    except Exception as e:
        print(f"Failed to get config: {e}")

if __name__ == "__main__":
    asyncio.run(check())
