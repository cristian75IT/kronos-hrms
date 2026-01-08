"""KRONOS Backend - Core Configuration."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─────────────────────────────────────────────────────────────
    # Application
    # ─────────────────────────────────────────────────────────────
    service_name: str = Field(default="kronos", alias="SERVICE_NAME")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )
    cors_origins: str = Field(
        default="*",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins, or '*' for all"
    )
    auto_fix_reconciliation: bool = Field(
        default=False,
        alias="AUTO_FIX_RECONCILIATION",
        description="Enable auto-fix for missing ledger entries during reconciliation"
    )

    # ─────────────────────────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://kronos:kronos_dev@localhost:5432/kronos",
        alias="DATABASE_URL",
    )
    database_schema: str = Field(default="public", alias="DATABASE_SCHEMA")
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # ─────────────────────────────────────────────────────────────
    # Redis
    # ─────────────────────────────────────────────────────────────
    redis_url: str = Field(
        default="redis://localhost:6379/0", alias="REDIS_URL"
    )

    # ─────────────────────────────────────────────────────────────
    # Keycloak SSO
    # ─────────────────────────────────────────────────────────────
    keycloak_url: str = Field(
        default="http://localhost:8080/", alias="KEYCLOAK_URL"
    )
    keycloak_realm: str = Field(default="kronos", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(
        default="kronos-backend", alias="KEYCLOAK_CLIENT_ID"
    )
    keycloak_client_secret: str = Field(
        default="", alias="KEYCLOAK_CLIENT_SECRET"
    )

    # ─────────────────────────────────────────────────────────────
    # MinIO
    # ─────────────────────────────────────────────────────────────
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="kronos", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="kronos_dev", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="kronos-attachments", alias="MINIO_BUCKET")
    minio_use_ssl: bool = Field(default=False, alias="MINIO_USE_SSL")

    # ─────────────────────────────────────────────────────────────
    # Brevo (Email)
    # ─────────────────────────────────────────────────────────────
    brevo_api_key: str = Field(default="", alias="BREVO_API_KEY")
    brevo_sender_email: str = Field(
        default="noreply@kronos.local", alias="BREVO_SENDER_EMAIL"
    )
    brevo_sender_name: str = Field(default="KRONOS HR", alias="BREVO_SENDER_NAME")

    # ─────────────────────────────────────────────────────────────
    # Service URLs (for inter-service communication)
    # ─────────────────────────────────────────────────────────────
    auth_service_url: str = Field(
        default="http://localhost:8001", alias="AUTH_SERVICE_URL"
    )
    config_service_url: str = Field(
        default="http://localhost:8004", alias="CONFIG_SERVICE_URL"
    )
    notification_service_url: str = Field(
        default="http://localhost:8005", alias="NOTIFICATION_SERVICE_URL"
    )
    audit_service_url: str = Field(
        default="http://localhost:8007", alias="AUDIT_SERVICE_URL"
    )
    calendar_service_url: str = Field(
        default="http://localhost:8009", alias="CALENDAR_SERVICE_URL"
    )
    leave_service_url: str = Field(
        default="http://localhost:8002", alias="LEAVE_SERVICE_URL"
    )
    expense_service_url: str = Field(
        default="http://localhost:8003", alias="EXPENSE_SERVICE_URL"
    )
    hr_reporting_service_url: str = Field(
        default="http://localhost:8011", alias="HR_REPORTING_SERVICE_URL"
    )
    approval_service_url: str = Field(
        default="http://localhost:8012", alias="APPROVAL_SERVICE_URL"
    )
    smart_working_service_url: str = Field(
        default="http://localhost:8013", alias="SMART_WORKING_SERVICE_URL"
    )
    
    # Internal service-to-service token for callback endpoints
    internal_service_token: str = Field(
        default="change-me-internal-token", alias="INTERNAL_SERVICE_TOKEN"
    )

    # ─────────────────────────────────────────────────────────────
    # VAPID (Web Push Notifications)
    # ─────────────────────────────────────────────────────────────
    vapid_private_key: str = Field(default="", alias="VAPID_PRIVATE_KEY")
    vapid_public_key: str = Field(default="", alias="VAPID_PUBLIC_KEY")
    vapid_subject: str = Field(default="mailto:admin@kronos.local", alias="VAPID_SUBJECT")

    # ─────────────────────────────────────────────────────────────
    # Frontend URL (for absolute links in emails/notifications)
    # ─────────────────────────────────────────────────────────────
    frontend_url: str = Field(
        default="http://localhost:3000", alias="FRONTEND_URL"
    )

    # ─────────────────────────────────────────────────────────────
    # Inter-Service Communication Settings
    # ─────────────────────────────────────────────────────────────
    service_timeout: float = Field(
        default=10.0, alias="SERVICE_TIMEOUT",
        description="Default timeout in seconds for inter-service HTTP calls"
    )
    service_max_retries: int = Field(
        default=3, alias="SERVICE_MAX_RETRIES",
        description="Maximum retry attempts for failed service calls"
    )
    service_pool_connections: int = Field(
        default=100, alias="SERVICE_POOL_CONNECTIONS",
        description="Maximum number of connections in the HTTP pool"
    )
    service_pool_keepalive: int = Field(
        default=20, alias="SERVICE_POOL_KEEPALIVE",
        description="Maximum number of keep-alive connections"
    )

    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        """Get CORS origins as list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
