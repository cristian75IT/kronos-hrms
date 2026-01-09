"""KRONOS Backend - Centralized Error Handlers.

Provides standard exception handling and error response formatting
for all microservices.
"""
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import (
    KronosException,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    BusinessRuleError,
    MissingConfigurationError,
)
from src.core.config import settings

# Import shared exceptions for unified handling
from src.shared.exceptions import MicroserviceError as SharedMicroserviceError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Response Schemas
# ═══════════════════════════════════════════════════════════

class ErrorDetails(BaseModel):
    """Detailed error info."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    error: ErrorDetails


# ═══════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════

def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> JSONResponse:
    """Create standardized JSON response."""
    # Get request ID from state (set by middleware) or generate new
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())) if request else str(uuid.uuid4())
    
    content = ErrorResponse(
        error=ErrorDetails(
            code=code,
            message=message,
            details=details,
            request_id=request_id,
        )
    ).model_dump(mode="json")
    
    return JSONResponse(
        status_code=status_code,
        content=content,
    )


# ═══════════════════════════════════════════════════════════
# Exception Handlers
# ═══════════════════════════════════════════════════════════

async def kronos_exception_handler(request: Request, exc: KronosException) -> JSONResponse:
    """Handle custom KRONOS exceptions."""
    # Map exception types to status codes
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, MissingConfigurationError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, BusinessRuleError):
        status_code = status.HTTP_400_BAD_REQUEST
    
    # Log business errors as warnings, system errors as errors
    if status_code < 500:
        logger.warning(f"{exc.code}: {exc.message} (URL: {request.url})")
    else:
        logger.error(f"{exc.code}: {exc.message} (URL: {request.url})")
        
    return create_error_response(
        status_code=status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        request=request,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI/Pydantic validation errors."""
    details = {}
    for error in exc.errors():
        # Get field name from loc (location)
        # loc is tuple like ('body', 'field_name', 'sub_field')
        loc = error.get("loc", [])
        field = ".".join([str(x) for x in loc[1:]]) if len(loc) > 1 else str(loc[-1]) if loc else "unknown"
        msg = error.get("msg", "Invalid value")
        
        if field in details:
            if isinstance(details[field], list):
                details[field].append(msg)
            else:
                details[field] = [details[field], msg]
        else:
            details[field] = msg
            
    logger.warning(f"Validation error at {request.url}: {details}")
            
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"fields": details},
        request=request,
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle Database errors."""
    error_msg = str(exc)
    code = "DATABASE_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if isinstance(exc, IntegrityError):
        code = "DATA_INTEGRITY_ERROR"
        status_code = status.HTTP_409_CONFLICT
        error_msg = "Data integrity violation (duplicate entry or constraint)"
    
    logger.error(f"Database error at {request.url}: {exc}")
    
    # Don't expose SQL details in production
    if settings.is_production:
        details = None
    else:
        details = {"original_error": str(exc)}
        
    return create_error_response(
        status_code=status_code,
        code=code,
        message=error_msg,
        details=details,
        request=request,
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    # Log full traceback
    logger.error(f"Unhandled exception at {request.url}: {exc}")
    logger.error(traceback.format_exc())
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"error": str(exc)} if not settings.is_production else None,
        request=request,
    )


async def microservice_exception_handler(request: Request, exc: SharedMicroserviceError) -> JSONResponse:
    """Handle shared MicroserviceError exceptions from shared/exceptions.py.
    
    This handler provides unified error handling for exceptions raised
    using the enterprise exception hierarchy in src.shared.exceptions.
    """
    # Log based on severity
    if exc.http_status >= 500:
        logger.error(f"{exc.code}: {exc.message} (URL: {request.url})")
    else:
        logger.warning(f"{exc.code}: {exc.message} (URL: {request.url})")
    
    return create_error_response(
        status_code=exc.http_status,
        code=exc.code,
        message=exc.message,
        details=exc.details if exc.details else None,
        request=request,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions (404, 405, etc.)."""
    return create_error_response(
        status_code=exc.status_code,
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        request=request,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers on the application.
    
    Handler order matters! More specific handlers should be registered first.
    The Exception handler should always be last as a catch-all.
    """
    # KRONOS core exceptions (legacy)
    app.add_exception_handler(KronosException, kronos_exception_handler)
    
    # Shared MicroserviceError hierarchy (enterprise standard)
    app.add_exception_handler(SharedMicroserviceError, microservice_exception_handler)
    
    # Framework & ORM exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Global catch-all (must be last)
    app.add_exception_handler(Exception, global_exception_handler)
