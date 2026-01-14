"""
KRONOS Approval Service - FastAPI Application.

Enterprise-grade approval workflow engine.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from .routers import (
    config_router,
    requests_router,
    decisions_router,
    internal_router,
)

app = FastAPI(
    title="KRONOS Approval Service",
    description="Enterprise Approval Workflow Engine - Flussi autorizzativi centralizzati",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register error handlers
from src.core.error_handlers import register_error_handlers
register_error_handlers(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(config_router, prefix="/api/v1/approvals")
app.include_router(requests_router, prefix="/api/v1/approvals")
app.include_router(decisions_router, prefix="/api/v1/approvals")
app.include_router(internal_router, prefix="/api/v1/approvals")
from .routers.setup import router as setup_router
app.include_router(setup_router, prefix="/api/v1/approvals")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "approval-service"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "KRONOS Approval Service",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "Enterprise Approval Workflow Engine",
    }
