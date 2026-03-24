"""Tests for InternalHTTPClient — covers call(), error handling, and lifecycle."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from ceramicraft_mcp_server.http_client import InternalHTTPClient, get_http_client


def test_get_http_client_singleton():
    """get_http_client returns the same instance."""
    import ceramicraft_mcp_server.http_client as mod

    mod._http_client = None
    c1 = get_http_client()
    c2 = get_http_client()
    assert c1 is c2
    mod._http_client = None  # cleanup


def test_internal_http_client_init():
    """Client starts with no underlying httpx client."""
    client = InternalHTTPClient()
    assert client._client is None


@pytest.mark.asyncio
async def test_get_client_creates_connection():
    """_get_client creates an httpx.AsyncClient lazily."""
    client = InternalHTTPClient()
    async_client = await client._get_client()
    assert isinstance(async_client, httpx.AsyncClient)
    await client.close()


@pytest.mark.asyncio
async def test_close_client():
    """close() shuts down the underlying client."""
    client = InternalHTTPClient()
    await client._get_client()
    assert client._client is not None
    await client.close()


# ─── Helper to create client with mocked transport ────────


def _make_client_with_mock() -> tuple[InternalHTTPClient, AsyncMock]:
    """Create an InternalHTTPClient with a mocked _get_client."""
    client = InternalHTTPClient()
    mock_async_client = AsyncMock(spec=httpx.AsyncClient)
    # Override _get_client to return our mock
    client._get_client = AsyncMock(return_value=mock_async_client)  # type: ignore[method-assign]
    return client, mock_async_client


# ─── call() success paths ──────────────────────────────────


@pytest.mark.asyncio
async def test_call_get_success():
    """Successful GET returns parsed JSON."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [1, 2, 3]}
    mock_http.request = AsyncMock(return_value=mock_response)

    result = await client.call("http://svc:8080", "GET", "/api/test")
    assert result == {"data": [1, 2, 3]}
    mock_http.request.assert_called_once_with(
        method="GET",
        url="http://svc:8080/api/test",
        params=None,
        json=None,
        headers={},
    )


@pytest.mark.asyncio
async def test_call_post_with_user_id():
    """POST with user_id sets X-Original-User-ID header."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}
    mock_http.request = AsyncMock(return_value=mock_response)

    result = await client.call(
        "http://svc:8080",
        "POST",
        "/api/create",
        user_id=42,
        json_body={"name": "test"},
    )
    assert result == {"ok": True}
    call_kwargs = mock_http.request.call_args
    assert call_kwargs.kwargs["headers"] == {"X-Original-User-ID": "42"}
    assert call_kwargs.kwargs["json"] == {"name": "test"}


@pytest.mark.asyncio
async def test_call_with_params():
    """GET with query params passes them through."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}
    mock_http.request = AsyncMock(return_value=mock_response)

    await client.call(
        "http://svc:8080",
        "GET",
        "/api/list",
        params={"limit": 10, "offset": 0},
    )
    call_kwargs = mock_http.request.call_args
    assert call_kwargs.kwargs["params"] == {"limit": 10, "offset": 0}


@pytest.mark.asyncio
async def test_call_204_no_content():
    """204 response returns success dict."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_http.request = AsyncMock(return_value=mock_response)

    result = await client.call("http://svc:8080", "DELETE", "/api/item/1")
    assert result == {"success": True}


# ─── call() error paths ───────────────────────────────────


@pytest.mark.asyncio
async def test_call_connect_error():
    """ConnectError raises ToolError."""
    client, mock_http = _make_client_with_mock()
    mock_http.request = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(ToolError, match="Cannot connect"):
        await client.call("http://svc:8080", "GET", "/api/test")


@pytest.mark.asyncio
async def test_call_timeout_error():
    """TimeoutException raises ToolError."""
    client, mock_http = _make_client_with_mock()
    mock_http.request = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))

    with pytest.raises(ToolError, match="timed out"):
        await client.call("http://svc:8080", "GET", "/api/test")


@pytest.mark.asyncio
async def test_call_generic_http_error():
    """Generic HTTPError raises ToolError."""
    client, mock_http = _make_client_with_mock()
    mock_http.request = AsyncMock(side_effect=httpx.HTTPError("something broke"))

    with pytest.raises(ToolError, match="HTTP request failed"):
        await client.call("http://svc:8080", "GET", "/api/test")


@pytest.mark.asyncio
async def test_call_404_error():
    """404 response raises ToolError with 'not found'."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "product not found"}
    mock_response.text = "product not found"
    mock_http.request = AsyncMock(return_value=mock_response)

    with pytest.raises(ToolError, match="not found"):
        await client.call("http://svc:8080", "GET", "/api/product/999")


@pytest.mark.asyncio
async def test_call_403_error():
    """403 response raises ToolError with 'Access denied'."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {"message": "forbidden"}
    mock_response.text = "forbidden"
    mock_http.request = AsyncMock(return_value=mock_response)

    with pytest.raises(ToolError, match="Access denied"):
        await client.call("http://svc:8080", "GET", "/api/admin")


@pytest.mark.asyncio
async def test_call_409_error():
    """409 response raises ToolError with 'Conflict'."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_response.json.return_value = {"message": "duplicate"}
    mock_response.text = "duplicate"
    mock_http.request = AsyncMock(return_value=mock_response)

    with pytest.raises(ToolError, match="Conflict"):
        await client.call("http://svc:8080", "POST", "/api/create")


@pytest.mark.asyncio
async def test_call_422_error():
    """422 response raises ToolError with 'Validation error'."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"message": "invalid input"}
    mock_response.text = "invalid input"
    mock_http.request = AsyncMock(return_value=mock_response)

    with pytest.raises(ToolError, match="Validation error"):
        await client.call("http://svc:8080", "POST", "/api/create")


@pytest.mark.asyncio
async def test_call_500_error():
    """500 response raises ToolError with 'Backend service error'."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "internal error"}
    mock_response.text = "internal error"
    mock_http.request = AsyncMock(return_value=mock_response)

    with pytest.raises(ToolError, match="Backend service error"):
        await client.call("http://svc:8080", "GET", "/api/test")


@pytest.mark.asyncio
async def test_call_error_non_json_body():
    """Error response with non-JSON body still raises ToolError."""
    client, mock_http = _make_client_with_mock()
    mock_response = MagicMock()
    mock_response.status_code = 502
    mock_response.json.side_effect = ValueError("not json")
    mock_response.text = "Bad Gateway"
    mock_http.request = AsyncMock(return_value=mock_response)

    with pytest.raises(ToolError, match="Backend service error"):
        await client.call("http://svc:8080", "GET", "/api/test")
