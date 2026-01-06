"""
KRONOS - Enterprise Exception Hierarchy

Standardized exceptions for all microservices providing:
- Typed error handling
- Consistent error codes
- Structured error details for debugging
- HTTP status code mapping

Usage:
    from src.shared.exceptions import NotFoundError, ValidationError
    
    raise NotFoundError("User", user_id)
    raise ValidationError("Email format is invalid", field="email")
"""
from typing import Optional, Any


# ═══════════════════════════════════════════════════════════════════════════
# Base Exception
# ═══════════════════════════════════════════════════════════════════════════

class MicroserviceError(Exception):
    """
    Base exception for all KRONOS microservice errors.
    
    Provides structured error information including:
    - message: Human-readable error description
    - code: Machine-readable error code for programmatic handling
    - details: Additional context for debugging
    - http_status: Suggested HTTP status code for API responses
    """
    
    http_status: int = 500
    code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None,
        http_status: Optional[int] = None,
    ):
        self.message = message
        if code:
            self.code = code
        if http_status:
            self.http_status = http_status
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Client/Integration Exceptions (for inter-service communication)
# ═══════════════════════════════════════════════════════════════════════════

class ServiceUnavailableError(MicroserviceError):
    """
    Raised when an upstream service is unreachable.
    
    Use this for network errors, timeouts, or connection failures.
    The caller should typically retry or return a 503 to the client.
    """
    
    http_status = 503
    code = "SERVICE_UNAVAILABLE"
    
    def __init__(
        self,
        service_name: str,
        original_error: Optional[str] = None,
    ):
        super().__init__(
            message=f"Service '{service_name}' is currently unavailable",
            details={
                "service": service_name,
                "original_error": original_error,
            },
        )
        self.service_name = service_name


class ServiceResponseError(MicroserviceError):
    """
    Raised when an upstream service returns an error response.
    
    Use this for 4xx/5xx responses from other services.
    """
    
    http_status = 502
    code = "UPSTREAM_SERVICE_ERROR"
    
    def __init__(
        self,
        service_name: str,
        status_code: int,
        response_body: Optional[str] = None,
    ):
        super().__init__(
            message=f"Service '{service_name}' returned error: {status_code}",
            details={
                "service": service_name,
                "status_code": status_code,
                "response": response_body,
            },
        )
        self.service_name = service_name
        self.status_code = status_code


class ServiceTimeoutError(ServiceUnavailableError):
    """Raised when a service call times out."""
    
    code = "SERVICE_TIMEOUT"
    
    def __init__(self, service_name: str, timeout_seconds: float):
        super().__init__(
            service_name=service_name,
            original_error=f"Timeout after {timeout_seconds}s",
        )
        self.timeout_seconds = timeout_seconds


# ═══════════════════════════════════════════════════════════════════════════
# Resource Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class NotFoundError(MicroserviceError):
    """
    Raised when a requested resource does not exist.
    
    Usage:
        raise NotFoundError("User", user_id)
        raise NotFoundError("LeaveRequest", request_id, "or it has been deleted")
    """
    
    http_status = 404
    code = "NOT_FOUND"
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[Any] = None,
        additional_info: Optional[str] = None,
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        if additional_info:
            message = f"{message} {additional_info}"
        
        super().__init__(
            message=message,
            details={
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
            },
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictError(MicroserviceError):
    """
    Raised for resource conflicts (duplicates, state violations).
    
    Usage:
        raise ConflictError("A leave request already exists for these dates")
        raise ConflictError("User with this email already exists", field="email")
    """
    
    http_status = 409
    code = "CONFLICT"
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        existing_id: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            details={
                "field": field,
                "existing_id": str(existing_id) if existing_id else None,
            },
        )
        self.field = field
        self.existing_id = existing_id


# ═══════════════════════════════════════════════════════════════════════════
# Validation Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class ValidationError(MicroserviceError):
    """
    Raised when input validation fails.
    
    Usage:
        raise ValidationError("Email format is invalid", field="email")
        raise ValidationError("Start date must be before end date", 
                              fields=["start_date", "end_date"])
    """
    
    http_status = 422
    code = "VALIDATION_ERROR"
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        fields: Optional[list[str]] = None,
        value: Optional[Any] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if fields:
            details["fields"] = fields
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(message=message, details=details)
        self.field = field
        self.fields = fields


class BusinessRuleError(MicroserviceError):
    """
    Raised when a business rule is violated.
    
    Use this for domain-specific validations that go beyond basic input validation.
    
    Usage:
        raise BusinessRuleError(
            "Cannot approve own leave request",
            rule="SELF_APPROVAL_FORBIDDEN"
        )
        raise BusinessRuleError(
            "Insufficient leave balance",
            rule="INSUFFICIENT_BALANCE",
            details={"required": 5, "available": 3}
        )
    """
    
    http_status = 400
    code = "BUSINESS_RULE_VIOLATION"
    
    def __init__(
        self,
        message: str,
        rule: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        full_details = details or {}
        if rule:
            full_details["rule"] = rule
        
        super().__init__(message=message, details=full_details)
        self.rule = rule


# ═══════════════════════════════════════════════════════════════════════════
# Authorization Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class UnauthorizedError(MicroserviceError):
    """Raised when authentication is required but missing or invalid."""
    
    http_status = 401
    code = "UNAUTHORIZED"
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message)


class ForbiddenError(MicroserviceError):
    """Raised when the user lacks permission to perform an action."""
    
    http_status = 403
    code = "FORBIDDEN"
    
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        required_permission: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
    ):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = str(resource_id)
        
        super().__init__(message=message, details=details)
        self.required_permission = required_permission


# ═══════════════════════════════════════════════════════════════════════════
# State/Workflow Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class InvalidStateError(MicroserviceError):
    """
    Raised when an operation is invalid for the current resource state.
    
    Usage:
        raise InvalidStateError(
            "Cannot approve a cancelled request",
            current_state="CANCELLED",
            allowed_states=["PENDING", "SUBMITTED"]
        )
    """
    
    http_status = 400
    code = "INVALID_STATE"
    
    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        allowed_states: Optional[list[str]] = None,
        action: Optional[str] = None,
    ):
        details = {}
        if current_state:
            details["current_state"] = current_state
        if allowed_states:
            details["allowed_states"] = allowed_states
        if action:
            details["action"] = action
        
        super().__init__(message=message, details=details)
        self.current_state = current_state
        self.allowed_states = allowed_states


class RateLimitError(MicroserviceError):
    """Raised when rate limit is exceeded."""
    
    http_status = 429
    code = "RATE_LIMIT_EXCEEDED"
    
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after_seconds: Optional[int] = None,
    ):
        details = {}
        if retry_after_seconds:
            details["retry_after_seconds"] = retry_after_seconds
        
        super().__init__(message=message, details=details)
        self.retry_after_seconds = retry_after_seconds


# ═══════════════════════════════════════════════════════════════════════════
# Convenience Aliases (backward compatibility with existing code)
# ═══════════════════════════════════════════════════════════════════════════

# These match the exceptions currently used in the codebase
KronosError = MicroserviceError
ResourceNotFoundError = NotFoundError
DuplicateResourceError = ConflictError
