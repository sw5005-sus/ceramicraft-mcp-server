"""Configuration for the MCP server."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # MCP Server Configuration
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8080

    # Internal gRPC endpoints (Python services)
    NOTIFICATION_MS_GRPC: str = Field(default="notification-ms-svc:50051")
    LOG_MS_GRPC: str = Field(default="log-ms-svc:50051")

    # Internal HTTP endpoints (Go services, port 8080)
    # Cluster-internal URLs — HTTP is safe within K8s network
    PRODUCT_MS_HTTP: str = Field(default="http://product-ms-svc:8080")  # NOSONAR
    ORDER_MS_HTTP: str = Field(default="http://order-ms-svc:8080")  # NOSONAR
    USER_MS_HTTP: str = Field(default="http://user-ms-svc:8080")  # NOSONAR
    COMMENT_MS_HTTP: str = Field(default="http://comment-ms-svc:8080")  # NOSONAR
    PAYMENT_MS_HTTP: str = Field(default="http://payment-ms-svc:8080")  # NOSONAR

    # Internal HTTP endpoints (Python services, port 8080)
    NOTIFICATION_MS_HTTP: str = Field(
        default="http://notification-ms-svc:8080"
    )  # NOSONAR

    # Zitadel (MCP-specific, prefixed to avoid conflict with other services)
    MCP_ZITADEL_ISSUER: str = Field(default="https://cerami-t6ihrd.us1.zitadel.cloud")
    MCP_ZITADEL_JWKS_URL: str = Field(
        default="https://cerami-t6ihrd.us1.zitadel.cloud/oauth/v2/keys"
    )
    MCP_ZITADEL_CLIENT_ID: str = Field(default="")
    MCP_ZITADEL_CLIENT_SECRET: str = Field(default="")


@lru_cache
def get_settings() -> Settings:
    return Settings()
