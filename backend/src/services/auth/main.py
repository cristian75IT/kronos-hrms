"""KRONOS Auth Service - Main Application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import init_db, close_db
from src.services.auth.router import router
from src.services.auth.router_organization import router as org_router
# Import models to register them with SQLAlchemy metadata
from src.services.auth import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="KRONOS Auth Service",
    description="Authentication and user management service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
from src.services.auth.routers.setup import router as setup_router
app.include_router(setup_router, prefix="/api/v1/auth")

# Signature Service (for local development unified mode)
from src.services.signature.router import router as signature_router
app.include_router(signature_router, prefix="/api/v1")

# Add Request Context Middleware (must be after CORS)
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
