"""Configuration for the MCP server."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MCP Server Configuration
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8080

    # Internal service endpoints (cluster DNS)
    PRODUCT_MS_GRPC: str = Field(default="product-ms-svc:5001")
    ORDER_MS_GRPC: str = Field(default="order-ms-svc:5001")
    USER_MS_GRPC: str = Field(default="user-ms-svc:5001")
    COMMENT_MS_GRPC: str = Field(default="comment-ms-svc:5001")
    PAYMENT_MS_GRPC: str = Field(default="payment-ms-svc:5001")
    NOTIFICATION_MS_GRPC: str = Field(default="notification-ms-svc:50051")
    LOG_MS_GRPC: str = Field(default="log-ms-svc:50051")

    # Internal HTTP endpoints (for services without gRPC)
    USER_MS_HTTP: str = Field(default="http://user-ms-svc:8080")

    # OAuth / Zitadel
    OAUTH_ISSUER_URL: str = Field(default="")
    OAUTH_JWKS_URL: str = Field(default="")


@lru_cache
def get_settings() -> Settings:
    return Settings()
