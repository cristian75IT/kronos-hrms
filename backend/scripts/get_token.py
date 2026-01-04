import httpx
import asyncio

async def get_token():
    async with httpx.AsyncClient(base_url="http://localhost:8001/api/v1") as client:
        # We need an admin user. Let's try to login as admin.
        # Usually credentials are in seed or env. 
        # But I can also just skip auth if I run inside a service with special trust? 
        # No, let's try to login.
        try:
            # Try to get user 1 if we know ID? No.
            # Let's try to login with common dev credentials
            resp = await client.post("/auth/login", data={
                "username": "admin",
                "password": "admin"
            })
            if resp.status_code == 200:
                print(resp.json()["access_token"])
            else:
                print(f"Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(get_token())
