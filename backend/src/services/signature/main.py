"""Signature Service Entry Point.

Enterprise-grade FastAPI application with:
- CORS configured from environment settings
- Proper middleware and error handling
- Health check endpoint for monitoring
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import init_db, close_db
from src.services.signature.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    await init_db()
    print(f"✅ Signature Service Started (env: {settings.environment})")
    yield
    # Shutdown
    await close_db()
    print("🛑 Signature Service Stopped")


app = FastAPI(
    title="KRONOS - Signature Service",
    description="""
    Enterprise Digital Signature & Claims Service.
    
    Provides legally binding digital signatures using MFA OTP verification.
    All signature transactions are immutable and include forensic metadata.
    """,
    version="1.0.0",
    docs_url="/api/v1/signature/docs",
    redoc_url="/api/v1/signature/redoc",
    openapi_url="/api/v1/signature/openapi.json",
    lifespan=lifespan
)

# CORS - Use settings for production-ready configuration
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include Router with prefix
app.include_router(router, prefix="/api/v1")

# Middleware & Error Handlers
from src.core.middleware import RequestContextMiddleware
app.add_middleware(RequestContextMiddleware)

from src.core.error_handlers import register_error_handlers
register_error_handlers(app)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "signature-service",
        "version": "1.0.0",
        "environment": settings.environment
    }
