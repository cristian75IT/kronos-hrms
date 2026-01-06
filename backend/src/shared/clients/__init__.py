"""
KRONOS - Enterprise Service Clients

This package provides optimized HTTP clients for inter-service communication.

Features:
- Connection pooling (shared across all clients)
- Typed exception handling
- Automatic retry for transient failures
- Configurable timeouts

Usage:
    from src.shared.clients import AuthClient, NotificationClient
    
    auth_client = AuthClient()
    user = await auth_client.get_user(user_id)

Backward Compatibility:
    All existing imports from `src.shared.clients` continue to work.
    The old monolithic `clients.py` is deprecated and will be removed.
"""

from src.shared.clients.base import BaseClient
from src.shared.clients.auth import AuthClient
from src.shared.clients.config import ConfigClient
from src.shared.clients.notification import NotificationClient
from src.shared.clients.calendar import CalendarClient
from src.shared.clients.approval import ApprovalClient

from src.shared.clients.leave import LeaveClient, LeavesClient
from src.shared.clients.expense import ExpenseClient

__all__ = [
    # Base
    "BaseClient",
    # Service Clients
    "AuthClient",
    "ConfigClient",
    "NotificationClient",
    "CalendarClient",

    "ApprovalClient",
    "LeaveClient",
    "LeavesClient",
    "ExpenseClient",
]

