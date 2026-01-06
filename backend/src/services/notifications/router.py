"""KRONOS Notification Service - API Router."""
from fastapi import APIRouter

from .routers import users, admin, internal

# Re-export notification service dependency for backward compatibility if needed, 
# though ideally should be imported from deps.py
from .deps import get_notification_service 

router = APIRouter()

# Include sub-routers
# Note: Tags are usually defined in main.py or here. 
# Previous router didn't seem to have explicit tags on specific endpoints, 
# but often services have a global tag. 
# I will not add specific tags to avoid cluttering Swagger with new tags unless requested.
router.include_router(users.router)
router.include_router(admin.router)
router.include_router(internal.router)
