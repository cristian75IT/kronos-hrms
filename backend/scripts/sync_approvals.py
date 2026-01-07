
import asyncio
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, text
from src.core.database import get_db_context, init_db
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus
from src.services.leaves.services import LeaveService
from src.services.leaves.balance_service import LeaveBalanceService
from src.services.leaves.schemas import ApproveRequest, ApproveConditionalRequest, BalanceAdjustment
from src.services.leaves.wallet.models import WalletTransaction

async def sync():
    await init_db()
    
    async with get_db_context() as session:
        service = LeaveService(session)
        balance_service = LeaveBalanceService(session)
        
        # 1. Initialize balances for ALL users with ANY leave request
        print("Checking for users needing balance initialization...")
        stmt_users = text("SELECT DISTINCT user_id FROM leaves.leave_requests")
        res_users = await session.execute(stmt_users)
        user_ids = [r[0] for r in res_users.all()]
        
        for user_id in user_ids:
            # Check current year
            year = 2026
            summary = await balance_service.get_balance_summary(user_id, year)
            
            # If no wallet exists OR balance is zero, initialize
            if summary.vacation_total_available == 0:
                print(f"  [BALANCE] Initializing user {user_id} with 30 days of vacation.")
                await balance_service.adjust_balance(
                    user_id=user_id,
                    year=year,
                    data=BalanceAdjustment(amount=Decimal("30"), balance_type="vacation_ac", reason="Repair initialization"),
                    admin_id=UUID("00000000-0000-0000-0000-000000000000")
                )

        # 2. Reconcile with Approvals service
        print("\nReconciling with Approvals service...")
        stmt_apps = text("SELECT id, entity_id, status, resolution_notes FROM approvals.approval_requests WHERE entity_type = 'LEAVE'")
        res_apps = await session.execute(stmt_apps)
        approvals = res_apps.all()

        for app_id, entity_id, app_status, notes in approvals:
            stmt_leave = select(LeaveRequest).where(LeaveRequest.id == entity_id)
            res_leave = await session.execute(stmt_leave)
            leave = res_leave.scalar_one_or_none()
            
            if not leave:
                continue
                
            print(f"Checking Leave {entity_id}: Leaf Status={leave.status}, App Status={app_status}")
            
            # If Leaf is PENDING but App is APPROVED/CONDITIONAL
            if leave.status == LeaveRequestStatus.PENDING and app_status in ("APPROVED", "APPROVED_CONDITIONAL"):
                print(f"  [SYNC] Fixing PENDING -> {app_status}")
                if app_status == "APPROVED":
                    await service.approve_request(entity_id, UUID("00000000-0000-0000-0000-000000000000"), ApproveRequest(notes=notes or "Sync repair"))
                else:
                    await service.approve_conditional(entity_id, UUID("00000000-0000-0000-0000-000000000000"), ApproveConditionalRequest(condition_type="ric", condition_details=notes or "Sync repair"))

            # If Leaf is APPROVED but MISSING transaction or flag is False
            if leave.status == LeaveRequestStatus.APPROVED:
                stmt_tx = select(WalletTransaction).where(WalletTransaction.reference_id == entity_id)
                res_tx = await session.execute(stmt_tx)
                has_tx = res_tx.scalars().first() is not None
                
                if not has_tx:
                    print(f"  [REPAIR] APPROVED request {entity_id} is missing transactions. Re-triggering deduction.")
                    await balance_service.deduct_balance(leave, leave.deduction_details or {"vacation": float(leave.days_requested)})
                    has_tx = True
                
                if has_tx and not leave.balance_deducted:
                    print(f"  [REPAIR] Updating balance_deducted flag for {entity_id}")
                    await session.execute(text("UPDATE leaves.leave_requests SET balance_deducted = TRUE WHERE id = :id"), {"id": entity_id})
                    await session.commit()
                    print(f"  [SUCCESS] Flag updated for {entity_id}")

    print("\nSync and Repair complete.")

if __name__ == "__main__":
    asyncio.run(sync())
