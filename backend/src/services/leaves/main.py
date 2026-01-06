"""KRONOS Leave Service - Main Application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import init_db, close_db
from src.services.leaves.router import router
# Enterprise routers
from src.services.leaves.routers.user_actions import router as user_router
from src.services.leaves.routers.approver_actions import router as approver_router
from src.services.leaves.routers.delegation import router as delegation_router
from src.services.leaves.routers.internal import router as internal_router
# Import models to register them with SQLAlchemy metadata
from src.services.leaves import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="KRONOS Leave Service",
    description="Leave requests and balance management service",
    version="2.0.0",  # Enterprise version
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Main router (backward compatible, includes calendar, requests, balances, reports)
app.include_router(router, prefix="/api/v1")

# Enterprise routers (specific modules)
app.include_router(user_router, prefix="/api/v1/leaves")
app.include_router(approver_router, prefix="/api/v1/leaves")
app.include_router(delegation_router, prefix="/api/v1/leaves")
app.include_router(internal_router, prefix="/api/v1/leaves")


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
        "service": settings.service_name,
        "schema": settings.database_schema,
    }
