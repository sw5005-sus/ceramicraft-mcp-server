"""Tests for configuration module."""

from ceramicraft_mcp_server.config import Settings, get_settings


def test_settings_defaults():
    """Settings should load with expected defaults."""
    settings = Settings()
    assert settings.MCP_SERVER_HOST == "0.0.0.0"
    assert settings.MCP_SERVER_PORT == 8080
    assert settings.PRODUCT_MS_HTTP == "http://product-ms-svc:8080"
    assert settings.ORDER_MS_HTTP == "http://order-ms-svc:8080"
    assert settings.USER_MS_HTTP == "http://user-ms-svc:8080"
    assert settings.COMMENT_MS_HTTP == "http://comment-ms-svc:8080"
    assert settings.PAYMENT_MS_HTTP == "http://payment-ms-svc:8080"
    assert settings.NOTIFICATION_MS_HTTP == "http://notification-ms-svc:8080"
    assert settings.LOG_MS_GRPC == "log-ms-svc:50051"
    assert settings.NOTIFICATION_MS_GRPC == "notification-ms-svc:50051"
    assert "cerami-t6ihrd.us1.zitadel.cloud" in settings.MCP_ZITADEL_ISSUER
    assert settings.MCP_ZITADEL_JWKS_URL.endswith("/oauth/v2/keys")


def test_get_settings_returns_settings_instance():
    """get_settings() should return a Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)


def test_get_settings_is_cached():
    """get_settings() should return the same object on repeated calls."""
    assert get_settings() is get_settings()
