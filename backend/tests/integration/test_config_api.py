import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(base_url="http://localhost/api/v1") as client:
        # 1. Try GET
        print("Testing GET /config/approval.auto_escalate")
        resp = await client.get("/config/approval.auto_escalate")
        print(f"GET status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"GET body: {resp.json()}")
        
        # 2. Try PUT
        print("\nTesting PUT /config/approval.auto_escalate")
        resp = await client.put("/config/approval.auto_escalate", json={"value": True})
        print(f"PUT status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"PUT error: {resp.text}")

        # 3. Try POST if missing
        if resp.status_code == 404:
            print("\nTesting POST /config")
            resp = await client.post("/config", json={
                "key": "approval.test_key",
                "value": True,
                "value_type": "boolean",
                "category": "test",
                "description": "test description"
            })
            print(f"POST status: {resp.status_code}")
            if resp.status_code == 201:
                print(f"POST body: {resp.json()}")
            else:
                print(f"POST error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test())
