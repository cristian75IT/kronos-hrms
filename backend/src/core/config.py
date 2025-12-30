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


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
