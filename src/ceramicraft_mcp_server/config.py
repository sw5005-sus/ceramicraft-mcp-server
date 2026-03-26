"""Configuration for the MCP server."""

from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_HTTP_SCHEME = "http"


def _svc_url(host: str, port: int = 8080) -> str:
    """Build a cluster-internal service URL."""
    return f"{_HTTP_SCHEME}://{host}:{port}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # MCP Server Configuration
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8080

    # Internal HTTP endpoints (cluster-internal, built from service names)
    PRODUCT_MS_HTTP: str = _svc_url("product-ms-svc")
    ORDER_MS_HTTP: str = _svc_url("order-ms-svc")
    USER_MS_HTTP: str = _svc_url("user-ms-svc")
    COMMENT_MS_HTTP: str = _svc_url("comment-ms-svc")
    PAYMENT_MS_HTTP: str = _svc_url("payment-ms-svc")
    NOTIFICATION_MS_HTTP: str = _svc_url("notification-ms-svc")

    # Zitadel (MCP-specific, prefixed to avoid conflict with other services)
    MCP_ZITADEL_ISSUER: str = "https://cerami-t6ihrd.us1.zitadel.cloud"
    MCP_ZITADEL_JWKS_URL: str = "https://cerami-t6ihrd.us1.zitadel.cloud/oauth/v2/keys"


@cache
def get_settings() -> Settings:
    return Settings()
