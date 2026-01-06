"""
Verify Refactoring of Expenses and Notifications Services.
Checks imports and instantiation.
"""
import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.services.expenses.services import ExpenseService
from src.services.notifications.services import NotificationService
from src.services.notifications.router import router as notification_router
from src.services.expenses.router import router as expense_router

async def verify():
    print("Verifying Refactoring...")
    
    mock_session = MagicMock()
    
    # 1. Expense Service
    try:
        print("Initializing ExpenseService...")
        expense_svc = ExpenseService(mock_session)
        print("✅ ExpenseService initialized.")
        assert hasattr(expense_svc, "create_trip"), "Missing create_trip in Facade"
    except Exception as e:
        print(f"❌ ExpenseService Validation Failed: {e}")
        sys.exit(1)

    # 2. Notification Service
    try:
        print("Initializing NotificationService...")
        notify_svc = NotificationService(mock_session)
        print("✅ NotificationService initialized.")
        assert hasattr(notify_svc, "send_email"), "Missing send_email in Facade"
        assert hasattr(notify_svc, "subscribe_to_push"), "Missing subscribe_to_push in Facade"
        assert hasattr(notify_svc, "_email"), "Missing _email sub-service"
        assert hasattr(notify_svc, "_core"), "Missing _core sub-service"
    except Exception as e:
        print(f"❌ NotificationService Validation Failed: {e}")
        sys.exit(1)

    # 3. Approvals Service
    try:
        from src.services.approvals.services import ApprovalService
        print("Initializing ApprovalService...")
        approval_svc = ApprovalService(mock_session)
        print("✅ ApprovalService initialized.")
        assert hasattr(approval_svc, "create_approval_request"), "Missing create_approval_request"
    except ImportError as e:
        print(f"❌ ApprovalService Import Failed: {e}")
    except Exception as e:
        print(f"❌ ApprovalService Validation Failed: {e}")
        sys.exit(1)

    # 4. Leaves Wallet Service (Integrated in Leaves)
    try:
        from src.services.leaves.wallet import WalletService
        print("Initializing Integrated WalletService...")
        wallet_svc = WalletService(mock_session)
        print("✅ Integrated WalletService initialized.")
        # Check repos existence
        assert hasattr(wallet_svc, "_wallet_repo"), "Missing _wallet_repo"
        assert hasattr(wallet_svc, "_txn_repo"), "Missing _txn_repo"
    except Exception as e:
        print(f"❌ Integrated WalletService Validation Failed: {e}")
        sys.exit(1)

    # 5. Expensive Wallet Service
    try:
        from src.services.expensive_wallet.service import TripWalletService
        print("Initializing TripWalletService...")
        trip_wallet_svc = TripWalletService(mock_session)
        print("✅ TripWalletService initialized.")
        assert hasattr(trip_wallet_svc, "_wallet_repo"), "Missing _wallet_repo"
        assert hasattr(trip_wallet_svc, "_txn_repo"), "Missing _txn_repo"
    except Exception as e:
        print(f"❌ TripWalletService Validation Failed: {e}")
        sys.exit(1)

    # 6. Check Router Imports (Standardization Check)
    try:
        print("Checking Router imports...")
        from src.services.notifications import router as notif_router
        from src.services.expenses import router as exp_router
        from src.services.expensive_wallet.routers import api_router as wallet_router
        print("✅ Routers imported successfully.")
    except Exception as e:
        print(f"❌ Router Import Failed: {e}")
        sys.exit(1)

    print("\nAll verifications passed!")

if __name__ == "__main__":
    asyncio.run(verify())
