from src.shared.exceptions import MicroserviceError


class NotificationException(MicroserviceError):
    """Base exception for notification service."""
    pass


class NotificationNotFound(NotificationException):
    http_status = 404
    code = "NOTIFICATION_NOT_FOUND"
    
    def __init__(self, detail: str = "Notification not found"):
        super().__init__(message=detail)


class TemplateNotFound(NotificationException):
    http_status = 404
    code = "TEMPLATE_NOT_FOUND"
    
    def __init__(self, detail: str = "Email template not found"):
        super().__init__(message=detail)


class ProviderConfigurationError(NotificationException):
    http_status = 500
    code = "PROVIDER_CONFIG_ERROR"
    
    def __init__(self, detail: str = "Provider configuration error"):
        super().__init__(message=detail)


class DailyEmailLimitExceeded(NotificationException):
    http_status = 429
    code = "DAILY_EMAIL_LIMIT_EXCEEDED"
    
    def __init__(self, detail: str = "Daily email limit exceeded"):
        super().__init__(message=detail)


class PushSubscriptionNotFound(NotificationException):
    http_status = 404
    code = "PUSH_SUBSCRIPTION_NOT_FOUND"
    
    def __init__(self, detail: str = "Push subscription not found"):
        super().__init__(message=detail)
