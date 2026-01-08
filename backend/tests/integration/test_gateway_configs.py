import httpx
import asyncio

async def test():
    keys = [
        'notify_leave_request',
        'notify_leave_approval',
        'notify_wallet_expiry',
        'push_approvals',
        'leaves.block_insufficient_balance',
        'smart_deduction_enabled',
        'approval.auto_escalate',
        'approval.reminder_enabled',
        'approval.allow_self_approval'
    ]
    
    # We'll use the gateway URL
    url = "http://localhost/api/v1"
    
    async with httpx.AsyncClient(base_url=url) as client:
        print(f"Testing against Gateway: {url}\n")
        for key in keys:
            # 1. Test GET
            resp = await client.get(f"/config/{key}")
            print(f"GET /config/{key}: {resp.status_code}")
            if resp.status_code != 200:
                print(f"  GET Error: {resp.text}")
            
            # 2. Test PUT (authenticated)
            # Since we can't easily get a real token, we'll try it unauthenticated first to see if it's 401 or 404
            resp = await client.put(f"/config/{key}", json={"value": True})
            print(f"PUT /config/{key}: {resp.status_code}")
            if resp.status_code != 200 and resp.status_code != 401:
                 print(f"  PUT Error: {resp.text}")
        
        # Also test with a key that definitely DOES NOT exist
        resp = await client.get("/config/key.that.does.not.exist")
        print(f"\nGET /config/key.that.does.not.exist: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test())
