"""Shared test fixtures and configuration."""

import os

# Set required env vars before any module imports Settings.
# These are cluster-internal URLs — no defaults in production config.
os.environ.setdefault("PRODUCT_MS_HTTP", "http://product-ms-svc:8080")
os.environ.setdefault("ORDER_MS_HTTP", "http://order-ms-svc:8080")
os.environ.setdefault("USER_MS_HTTP", "http://user-ms-svc:8080")
os.environ.setdefault("COMMENT_MS_HTTP", "http://comment-ms-svc:8080")
os.environ.setdefault("PAYMENT_MS_HTTP", "http://payment-ms-svc:8080")
os.environ.setdefault("NOTIFICATION_MS_HTTP", "http://notification-ms-svc:8080")
