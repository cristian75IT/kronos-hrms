from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from .routers import api_router

app = FastAPI(
    title="KRONOS Expensive Wallet Service",
    description="Microservice dedicated to managing finances associated with Business Trips (Trasferte).",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


# Add Request Context Middleware
from src.core.middleware import RequestContextMiddleware
app.add_middleware(RequestContextMiddleware)

# Register Error Handlers
from src.core.error_handlers import register_error_handlers
register_error_handlers(app)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "expensive-wallet-service"}
