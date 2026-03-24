"""Tests for internal HTTP client."""

import pytest

from ceramicraft_mcp_server.http_client import InternalHTTPClient, get_http_client


def test_get_http_client_singleton():
    """get_http_client() should return the same instance."""
    client1 = get_http_client()
    client2 = get_http_client()
    assert client1 is client2


def test_internal_http_client_init():
    """Client should start with no underlying connection."""
    client = InternalHTTPClient()
    assert client._client is None


@pytest.mark.anyio
async def test_get_client_creates_connection():
    """_get_client() should create a connection lazily."""
    client = InternalHTTPClient()
    http_client = await client._get_client()
    assert http_client is not None
    assert not http_client.is_closed
    await client.close()


@pytest.mark.anyio
async def test_close_client():
    """close() should close the underlying connection."""
    client = InternalHTTPClient()
    await client._get_client()
    await client.close()
    assert client._client is not None
    assert client._client.is_closed
