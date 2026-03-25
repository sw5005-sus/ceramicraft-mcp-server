"""Tests for configuration module."""

import os
from unittest.mock import patch

from ceramicraft_mcp_server.config import Settings, get_settings

# Required env vars for Settings (no defaults — injected via Vault in prod)
_TEST_HTTP_ENV = {
    "PRODUCT_MS_HTTP": "http://product-ms-svc:8080",
    "ORDER_MS_HTTP": "http://order-ms-svc:8080",
    "USER_MS_HTTP": "http://user-ms-svc:8080",
    "COMMENT_MS_HTTP": "http://comment-ms-svc:8080",
    "PAYMENT_MS_HTTP": "http://payment-ms-svc:8080",
    "NOTIFICATION_MS_HTTP": "http://notification-ms-svc:8080",
}


def test_settings_with_env():
    """Settings should load when required env vars are present."""
    with patch.dict(os.environ, _TEST_HTTP_ENV):
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


def test_settings_missing_required_env():
    """Settings should fail if required HTTP env vars are missing."""
    import pytest

    # Remove the keys that conftest set
    clean_env = {k: v for k, v in os.environ.items() if not k.endswith("_MS_HTTP")}
    with patch.dict(os.environ, clean_env, clear=True), pytest.raises(Exception):
        Settings()


def test_get_settings_returns_settings_instance():
    """get_settings() should return a Settings instance."""
    with patch.dict(os.environ, _TEST_HTTP_ENV):
        get_settings.cache_clear()
        settings = get_settings()
    assert isinstance(settings, Settings)
    get_settings.cache_clear()


def test_get_settings_is_cached():
    """get_settings() should return the same object on repeated calls."""
    with patch.dict(os.environ, _TEST_HTTP_ENV):
        get_settings.cache_clear()
        assert get_settings() is get_settings()
    get_settings.cache_clear()
