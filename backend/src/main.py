"""KRONOS Backend - Unified Development Gateway.

This module provides a single FastAPI application that includes all service
routers for local development convenience. In production, each service runs
as a separate microservice behind the API gateway (Nginx).

NOTE: Services are added incrementally. If import fails, comment out
the problematic service and investigate separately.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    await init_db()
    print(f"✅ KRONOS Backend Started (env: {settings.environment})")
    yield
    await close_db()
    print("🛑 KRONOS Backend Stopped")


app = FastAPI(
    title="KRONOS Backend - Development Gateway",
    description="Unified backend for local development",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Core Services - Always included
# ============================================================================

# Auth Service
from src.services.auth.router import router as auth_router
from src.services.auth.router_organization import router as org_router
app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")

try:
    from src.services.auth.routers.setup import router as setup_router
    app.include_router(setup_router, prefix="/api/v1/auth")
except ImportError as e:
    print(f"⚠️ Auth setup router not loaded: {e}")

# Signature Service
from src.services.signature.router import router as signature_router
app.include_router(signature_router, prefix="/api/v1")

# ============================================================================
# Optional Services - May fail if dependencies missing
# ============================================================================

try:
    from src.services.leaves.router import router as leaves_router
    app.include_router(leaves_router, prefix="/api/v1")
except ImportError as e:
    print(f"⚠️ Leaves router not loaded: {e}")

try:
    from src.services.calendar.router import router as calendar_router
    app.include_router(calendar_router, prefix="/api/v1")
except ImportError as e:
    print(f"⚠️ Calendar router not loaded: {e}")

try:
    from src.services.notifications.router import router as notifications_router
    app.include_router(notifications_router, prefix="/api/v1")
except ImportError as e:
    print(f"⚠️ Notifications router not loaded: {e}")

try:
    from src.services.config.router import router as config_router
    app.include_router(config_router, prefix="/api/v1")
except ImportError as e:
    print(f"⚠️ Config router not loaded: {e}")

try:
    from src.services.audit.router import router as audit_router
    app.include_router(audit_router, prefix="/api/v1")
except ImportError as e:
    print(f"⚠️ Audit router not loaded: {e}")

try:
    from src.services.expenses.router import router as expenses_router
    app.include_router(expenses_router, prefix="/api/v1")
except ImportError as e:
    print(f"⚠️ Expenses router not loaded: {e}")

try:
    from src.services.approvals.routers import (
        config_router as approvals_config_router,
        requests_router as approvals_requests_router,
        decisions_router as approvals_decisions_router,
        internal_router as approvals_internal_router,
    )
    app.include_router(approvals_config_router, prefix="/api/v1/approvals")
    app.include_router(approvals_requests_router, prefix="/api/v1/approvals")
    app.include_router(approvals_decisions_router, prefix="/api/v1/approvals")
    app.include_router(approvals_internal_router, prefix="/api/v1/approvals")
except ImportError as e:
    print(f"⚠️ Approvals router not loaded: {e}")

# Add Request Context Middleware
from src.core.middleware import RequestContextMiddleware
app.add_middleware(RequestContextMiddleware)

# Register Error Handlers
from src.core.error_handlers import register_error_handlers
register_error_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "kronos-gateway",
        "environment": settings.environment,
    }
