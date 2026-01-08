from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import init_db, close_db
from src.services.smart_working.router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("Smart Working Service Started")
    yield
    # Shutdown
    await close_db()
    print("Smart Working Service Stopped")

app = FastAPI(
    title="KRONOS - Smart Working Service",
    description="Microservice for Remote Work (Lavoro Agile) management",
    version="1.0.0",
    docs_url="/api/v1/smart-working/docs",
    openapi_url="/api/v1/smart-working/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(router, prefix="/api/v1")

# Add Request Context Middleware
from src.core.middleware import RequestContextMiddleware
app.add_middleware(RequestContextMiddleware)

# Register Error Handlers
from src.core.error_handlers import register_error_handlers
register_error_handlers(app)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "smart-working-service",
        "schema": settings.database_schema
    }
