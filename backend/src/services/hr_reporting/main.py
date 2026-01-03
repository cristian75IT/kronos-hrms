"""
KRONOS HR Reporting Service - FastAPI Application.

Enterprise HR analytics and reporting service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from .routers import dashboard_router, reports_router, admin_router

app = FastAPI(
    title="KRONOS HR Reporting Service",
    description="Enterprise HR Analytics, Dashboards, and Compliance Reporting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(dashboard_router, prefix="/api/v1/hr")
app.include_router(reports_router, prefix="/api/v1/hr")
app.include_router(admin_router, prefix="/api/v1/hr")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "hr-reporting"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "KRONOS HR Reporting Service",
        "version": "1.0.0",
        "docs": "/docs",
    }
