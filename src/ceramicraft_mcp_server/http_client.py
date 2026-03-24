"""Internal HTTP client for calling Go backend services.

Go services use X-Original-User-ID header for user identity injection,
set by Traefik forwardAuth in production. MCP Server sets this header
directly when making internal cluster calls.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class InternalHTTPClient:
    """Makes authenticated HTTP calls to Go backend services."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30)
        return self._client

    async def call(
        self,
        base_url: str,
        method: str,
        path: str,
        *,
        user_id: int | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to an internal Go service.

        Args:
            base_url: Service base URL, e.g. "http://product-ms-svc:8080".
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API path, e.g. "/product-ms/v1/customer/products".
            user_id: User ID to inject via X-Original-User-ID header.
            params: Query parameters.
            json_body: JSON request body.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            httpx.HTTPStatusError: On 4xx/5xx responses.
        """
        headers: dict[str, str] = {}
        if user_id is not None:
            headers["X-Original-User-ID"] = str(user_id)

        client = await self._get_client()
        url = f"{base_url}{path}"

        logger.debug("Internal HTTP %s %s user_id=%s", method, url, user_id)

        response = await client.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=headers,
        )
        response.raise_for_status()

        if response.status_code == 204:
            return {"success": True}

        result: dict[str, Any] = response.json()
        return result

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()


# Module-level singleton
_http_client: InternalHTTPClient | None = None


def get_http_client() -> InternalHTTPClient:
    """Get the shared InternalHTTPClient instance."""
    global _http_client
    if _http_client is None:
        _http_client = InternalHTTPClient()
    return _http_client
