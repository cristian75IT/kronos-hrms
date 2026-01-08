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
    
    async with httpx.AsyncClient(base_url="http://localhost:8004/api/v1") as client:
        for key in keys:
            resp = await client.get(f"/config/{key}")
            print(f"GET /config/{key}: {resp.status_code}")
            if resp.status_code != 200:
                print(f"  Error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test())
