import asyncio
import httpx
from datetime import date

async def test_endpoints():
    base_url = "http://localhost/api/v1/calendar"
    # We need a token. Since I don't have one easily, I'll just check if they are reachable (expect 401/403 or 200 if no auth implemented for some)
    # Actually most have Depends(get_current_user)
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1. Holidays list
        print("Testing /holidays-list...")
        try:
            resp = await client.get(f"{base_url}/holidays-list?year=2024")
            print(f"Holidays status: {resp.status_code}")
        except Exception as e:
            print(f"Holidays failed: {e}")

        # 2. Closures list
        print("\nTesting /closures-list...")
        try:
            resp = await client.get(f"{base_url}/closures-list?year=2024")
            print(f"Closures status: {resp.status_code}")
        except Exception as e:
            print(f"Closures failed: {e}")

        # 3. Exceptions
        print("\nTesting /exceptions...")
        try:
            resp = await client.get(f"{base_url}/exceptions?year=2024")
            print(f"Exceptions status: {resp.status_code}")
        except Exception as e:
            print(f"Exceptions failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
