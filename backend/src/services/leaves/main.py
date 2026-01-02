"""KRONOS Leave Service - Main Application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import init_db, close_db
from src.services.leaves.router import router
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
    version="1.0.0",
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

app.include_router(router, prefix="/api/v1")

# Add Request Context Middleware
from src.core.middleware import RequestContextMiddleware
app.add_middleware(RequestContextMiddleware)

import logging
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log any unhandled exception."""
    logger.error(f"Unhandled exception in {settings.service_name}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "msg": str(exc)},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "schema": settings.database_schema,
    }
