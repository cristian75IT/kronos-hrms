"""KRONOS Backend - Custom Exceptions."""
from typing import Any


class KronosException(Exception):
    """Base exception for KRONOS application."""

    def __init__(
        self,
        message: str,
        code: str = "KRONOS_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(KronosException):
    """Entity not found exception."""

    def __init__(
        self,
        message: str = "Resource not found",
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> None:
        details = {}
        if entity_type:
            details["entity_type"] = entity_type
        if entity_id:
            details["entity_id"] = entity_id
        super().__init__(message=message, code="NOT_FOUND", details=details)


class ValidationError(KronosException):
    """Validation error exception."""

    def __init__(
        self,
        message: str = "Validation error",
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message=message, code="VALIDATION_ERROR", details=error_details)


class AuthenticationError(KronosException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(KronosException):
    """Authorization error exception."""

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class ConflictError(KronosException):
    """Conflict error exception (e.g., duplicate, overlapping dates)."""

    def __init__(
        self,
        message: str = "Conflict detected",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, code="CONFLICT_ERROR", details=details)


class BusinessRuleError(KronosException):
    """Business rule violation exception."""

    def __init__(
        self,
        message: str,
        rule: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = details or {}
        if rule:
            error_details["rule"] = rule
        super().__init__(message=message, code="BUSINESS_RULE_ERROR", details=error_details)


class InsufficientBalanceError(BusinessRuleError):
    """Insufficient leave balance exception."""

    def __init__(
        self,
        message: str = "Insufficient balance",
        balance_type: str | None = None,
        available: float | None = None,
        requested: float | None = None,
    ) -> None:
        details = {}
        if balance_type:
            details["balance_type"] = balance_type
        if available is not None:
            details["available"] = available
        if requested is not None:
            details["requested"] = requested
        super().__init__(message=message, rule="BALANCE_CHECK", details=details)


class ExternalServiceError(KronosException):
    """External service error exception."""

    def __init__(
        self,
        message: str = "External service error",
        service: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = details or {}
        if service:
            error_details["service"] = service
        super().__init__(message=message, code="EXTERNAL_SERVICE_ERROR", details=error_details)


class MissingConfigurationError(KronosException):
    """
    Missing configuration error exception.
    
    Raised when a required system configuration is missing.
    Maps to HTTP 503 Service Unavailable with actionable guidance.
    
    Enterprise Pattern: Fail Fast & Loud - operations must not proceed
    silently when required configuration is absent.
    """

    def __init__(
        self,
        config_type: str,
        message: str | None = None,
        guidance: str | None = None,
    ) -> None:
        default_guidance = "Contatta l'amministratore di sistema per configurare questa funzionalità."
        details = {
            "config_type": config_type,
            "guidance": guidance or default_guidance,
        }
        
        default_message = f"Configurazione mancante: {config_type}. Funzionalità non disponibile."
        super().__init__(
            message=message or default_message,
            code="CONFIG_MISSING",
            details=details
        )
