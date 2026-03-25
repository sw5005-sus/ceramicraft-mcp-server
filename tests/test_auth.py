"""Tests for authentication and authorization module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import jwt as pyjwt
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from ceramicraft_mcp_server.auth import (
    AuthError,
    AuthenticatedUser,
    JWKSClient,
    _extract_bearer_token,
    _extract_roles,
    _find_key,
    require_admin,
    require_user,
    verify_token,
)


# ─── AuthenticatedUser ─────────────────────────────────────


def test_authenticated_user_defaults():
    """Default AuthenticatedUser has empty roles."""
    user = AuthenticatedUser(user_id="123")
    assert user.user_id == "123"
    assert user.roles == []
    assert user.email == ""
    assert user.name == ""
    assert not user.is_admin
    assert user.user_id_int == 123


def test_authenticated_user_admin_role():
    """User with merchant_admin role is recognized as admin."""
    user = AuthenticatedUser(user_id="1", roles=["merchant_admin", "user"])
    assert user.is_admin


def test_authenticated_user_product_auditor_role():
    """User with product_auditor role is recognized as admin."""
    user = AuthenticatedUser(user_id="1", roles=["product_auditor"])
    assert user.is_admin


def test_authenticated_user_product_editor_role():
    """User with product_editor role is recognized as admin."""
    user = AuthenticatedUser(user_id="1", roles=["product_editor"])
    assert user.is_admin


def test_authenticated_user_non_admin():
    """User without admin roles is not admin."""
    user = AuthenticatedUser(user_id="1", roles=["customer", "user"])
    assert not user.is_admin


def test_authenticated_user_id_int_invalid():
    """Non-numeric user_id returns 0."""
    user = AuthenticatedUser(user_id="not-a-number")
    assert user.user_id_int == 0


def test_authenticated_user_id_int_empty():
    """Empty user_id returns 0."""
    user = AuthenticatedUser(user_id="")
    assert user.user_id_int == 0


# ─── _find_key ─────────────────────────────────────────────


def test_find_key_exists():
    """Finds a key by kid."""
    jwks = {"keys": [{"kid": "k1", "n": "abc"}, {"kid": "k2", "n": "def"}]}
    assert _find_key(jwks, "k1") == {"kid": "k1", "n": "abc"}


def test_find_key_missing():
    """Returns None if kid not found."""
    jwks = {"keys": [{"kid": "k1"}]}
    assert _find_key(jwks, "k999") is None


def test_find_key_empty():
    """Returns None if keys list is empty."""
    assert _find_key({"keys": []}, "k1") is None
    assert _find_key({}, "k1") is None


# ─── _extract_roles ────────────────────────────────────────


def test_extract_roles_zitadel_format():
    """Extracts roles from Zitadel claim format."""
    payload = {
        "urn:zitadel:iam:org:project:roles": {
            "admin": {"orgId": "123"},
            "user": {"orgId": "123"},
        }
    }
    roles = _extract_roles(payload)
    assert set(roles) == {"admin", "user"}


def test_extract_roles_empty():
    """Returns empty list if no roles claim."""
    assert _extract_roles({}) == []
    assert _extract_roles({"other": "claim"}) == []


def test_extract_roles_non_dict():
    """Returns empty list if roles claim is not a dict."""
    assert _extract_roles({"urn:zitadel:iam:org:project:roles": "not-a-dict"}) == []
    assert _extract_roles({"urn:zitadel:iam:org:project:roles": ["a", "b"]}) == []


# ─── JWKSClient ────────────────────────────────────────────


def test_jwks_client_init():
    """JWKSClient starts with no cached data."""
    client = JWKSClient("https://example.com/keys")
    assert client._jwks_data is None


def test_jwks_client_invalidate():
    """invalidate() clears cached keys."""
    client = JWKSClient("https://example.com/keys")
    client._jwks_data = {"keys": []}
    client.invalidate()
    assert client._jwks_data is None


@pytest.mark.asyncio
async def test_jwks_client_fetches_keys():
    """get_signing_keys fetches from endpoint on first call."""
    client = JWKSClient("https://example.com/keys")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"keys": [{"kid": "k1"}]}
    mock_resp.raise_for_status = MagicMock()

    with patch("ceramicraft_mcp_server.auth.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        keys = await client.get_signing_keys()
        assert keys == {"keys": [{"kid": "k1"}]}
        mock_http.get.assert_called_once()


@pytest.mark.asyncio
async def test_jwks_client_caches_keys():
    """Second call uses cached data, no HTTP request."""
    client = JWKSClient("https://example.com/keys")
    client._jwks_data = {"keys": [{"kid": "cached"}]}

    keys = await client.get_signing_keys()
    assert keys == {"keys": [{"kid": "cached"}]}


# ─── _extract_bearer_token ─────────────────────────────────


def test_extract_bearer_token_from_headers():
    """Extract token from ctx.headers."""
    ctx = MagicMock()
    ctx.headers = {"authorization": "Bearer abc123"}
    ctx.meta = None
    assert _extract_bearer_token(ctx) == "abc123"


def test_extract_bearer_token_from_meta_extra():
    """Extract token from ctx.meta.extra dict."""
    ctx = MagicMock()
    ctx.headers = None
    ctx.meta.extra = {"token": "xyz789"}
    assert _extract_bearer_token(ctx) == "xyz789"


def test_extract_bearer_token_from_meta_authorization():
    """Extract token from ctx.meta.extra authorization field."""
    ctx = MagicMock()
    ctx.headers = None
    ctx.meta.extra = {"authorization": "Bearer tok456"}
    assert _extract_bearer_token(ctx) == "tok456"


def test_extract_bearer_token_none():
    """Returns None when no token found."""
    ctx = MagicMock()
    ctx.headers = {}
    ctx.meta = None
    assert _extract_bearer_token(ctx) is None


def test_extract_bearer_token_no_headers_attr():
    """Returns None gracefully if ctx has no headers attr."""
    ctx = MagicMock(spec=[])  # no attributes
    assert _extract_bearer_token(ctx) is None


def test_extract_bearer_token_non_bearer():
    """Returns None if Authorization is not Bearer."""
    ctx = MagicMock()
    ctx.headers = {"authorization": "Basic abc123"}
    ctx.meta = None
    assert _extract_bearer_token(ctx) is None


# ─── require_user / require_admin ──────────────────────────


@pytest.mark.asyncio
async def test_require_user_no_token():
    """require_user raises ToolError when no token."""
    ctx = MagicMock()
    ctx.headers = {}
    ctx.meta = None

    with pytest.raises(ToolError, match="Authentication required"):
        await require_user(ctx)


@pytest.mark.asyncio
async def test_require_user_invalid_token():
    """require_user raises ToolError on auth failure."""
    ctx = MagicMock()
    ctx.headers = {"authorization": "Bearer invalid.token.here"}
    ctx.meta = None

    with patch(
        "ceramicraft_mcp_server.auth.verify_token",
        AsyncMock(side_effect=AuthError("bad token")),
    ):
        with pytest.raises(ToolError, match="Authentication failed"):
            await require_user(ctx)


@pytest.mark.asyncio
async def test_require_user_success():
    """require_user returns user on valid token."""
    ctx = MagicMock()
    ctx.headers = {"authorization": "Bearer valid.token"}
    ctx.meta = None
    expected_user = AuthenticatedUser(user_id="42", roles=["customer"])

    with patch(
        "ceramicraft_mcp_server.auth.verify_token",
        AsyncMock(return_value=expected_user),
    ):
        user = await require_user(ctx)
        assert user.user_id == "42"


@pytest.mark.asyncio
async def test_require_admin_non_admin():
    """require_admin raises ToolError for non-admin user."""
    ctx = MagicMock()
    ctx.headers = {"authorization": "Bearer valid.token"}
    ctx.meta = None
    non_admin = AuthenticatedUser(user_id="42", roles=["customer"])

    with patch(
        "ceramicraft_mcp_server.auth.verify_token",
        AsyncMock(return_value=non_admin),
    ):
        with pytest.raises(ToolError, match="Admin access required"):
            await require_admin(ctx)


@pytest.mark.asyncio
async def test_require_admin_success():
    """require_admin returns user with admin role."""
    ctx = MagicMock()
    ctx.headers = {"authorization": "Bearer valid.token"}
    ctx.meta = None
    admin = AuthenticatedUser(user_id="1", roles=["merchant_admin"])

    with patch(
        "ceramicraft_mcp_server.auth.verify_token",
        AsyncMock(return_value=admin),
    ):
        user = await require_admin(ctx)
        assert user.is_admin


# ─── verify_token ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_token_expired():
    """verify_token raises AuthError for expired token."""
    with (
        patch(
            "ceramicraft_mcp_server.auth.jwt.get_unverified_header",
            return_value={"kid": "k1", "alg": "RS256"},
        ),
        patch("ceramicraft_mcp_server.auth._get_jwks_client") as mock_get_jwks,
    ):
        mock_jwks = AsyncMock()
        mock_jwks.get_signing_keys = AsyncMock(
            return_value={"keys": [{"kid": "k1", "kty": "RSA"}]}
        )
        mock_get_jwks.return_value = mock_jwks

        with (
            patch(
                "ceramicraft_mcp_server.auth.jwt.algorithms.RSAAlgorithm.from_jwk",
                return_value=MagicMock(),
            ),
            patch(
                "ceramicraft_mcp_server.auth.jwt.decode",
                side_effect=pyjwt.ExpiredSignatureError("expired"),
            ),
        ):
            with pytest.raises(AuthError, match="expired"):
                await verify_token("some.expired.token")


@pytest.mark.asyncio
async def test_verify_token_invalid_issuer():
    """verify_token raises AuthError for wrong issuer."""
    with (
        patch(
            "ceramicraft_mcp_server.auth.jwt.get_unverified_header",
            return_value={"kid": "k1", "alg": "RS256"},
        ),
        patch("ceramicraft_mcp_server.auth._get_jwks_client") as mock_get_jwks,
    ):
        mock_jwks = AsyncMock()
        mock_jwks.get_signing_keys = AsyncMock(return_value={"keys": [{"kid": "k1"}]})
        mock_get_jwks.return_value = mock_jwks

        with (
            patch(
                "ceramicraft_mcp_server.auth.jwt.algorithms.RSAAlgorithm.from_jwk",
                return_value=MagicMock(),
            ),
            patch(
                "ceramicraft_mcp_server.auth.jwt.decode",
                side_effect=pyjwt.InvalidIssuerError("bad issuer"),
            ),
        ):
            with pytest.raises(AuthError, match="issuer"):
                await verify_token("bad.issuer.token")


@pytest.mark.asyncio
async def test_verify_token_no_kid():
    """verify_token raises AuthError when kid missing from header."""
    with patch(
        "ceramicraft_mcp_server.auth.jwt.get_unverified_header",
        return_value={"alg": "RS256"},
    ):
        with pytest.raises(AuthError, match="kid"):
            await verify_token("no.kid.token")


@pytest.mark.asyncio
async def test_verify_token_key_not_found():
    """verify_token raises AuthError when kid not in JWKS."""
    with (
        patch(
            "ceramicraft_mcp_server.auth.jwt.get_unverified_header",
            return_value={"kid": "unknown", "alg": "RS256"},
        ),
        patch("ceramicraft_mcp_server.auth._get_jwks_client") as mock_get_jwks,
    ):
        mock_jwks = AsyncMock()
        mock_jwks.get_signing_keys = AsyncMock(
            return_value={"keys": [{"kid": "different"}]}
        )
        mock_jwks.invalidate = MagicMock()
        mock_get_jwks.return_value = mock_jwks

        with pytest.raises(AuthError, match="No matching key"):
            await verify_token("unknown.kid.token")


@pytest.mark.asyncio
async def test_verify_token_success():
    """verify_token returns AuthenticatedUser on valid token."""
    with (
        patch(
            "ceramicraft_mcp_server.auth.jwt.get_unverified_header",
            return_value={"kid": "k1", "alg": "RS256"},
        ),
        patch("ceramicraft_mcp_server.auth._get_jwks_client") as mock_get_jwks,
    ):
        mock_jwks = AsyncMock()
        mock_jwks.get_signing_keys = AsyncMock(return_value={"keys": [{"kid": "k1"}]})
        mock_get_jwks.return_value = mock_jwks

        with (
            patch(
                "ceramicraft_mcp_server.auth.jwt.algorithms.RSAAlgorithm.from_jwk",
                return_value=MagicMock(),
            ),
            patch(
                "ceramicraft_mcp_server.auth.jwt.decode",
                return_value={
                    "sub": "42",
                    "email": "test@example.com",
                    "name": "Test User",
                    "urn:zitadel:iam:org:project:roles": {
                        "merchant_admin": {"orgId": "1"},
                    },
                },
            ),
        ):
            user = await verify_token("valid.token")
            assert user.user_id == "42"
            assert user.email == "test@example.com"
            assert user.name == "Test User"
            assert "merchant_admin" in user.roles
            assert user.is_admin


@pytest.mark.asyncio
async def test_verify_token_decode_error():
    """verify_token raises AuthError on decode failure."""
    with (
        patch(
            "ceramicraft_mcp_server.auth.jwt.get_unverified_header",
            return_value={"kid": "k1", "alg": "RS256"},
        ),
        patch("ceramicraft_mcp_server.auth._get_jwks_client") as mock_get_jwks,
    ):
        mock_jwks = AsyncMock()
        mock_jwks.get_signing_keys = AsyncMock(return_value={"keys": [{"kid": "k1"}]})
        mock_get_jwks.return_value = mock_jwks

        with (
            patch(
                "ceramicraft_mcp_server.auth.jwt.algorithms.RSAAlgorithm.from_jwk",
                return_value=MagicMock(),
            ),
            patch(
                "ceramicraft_mcp_server.auth.jwt.decode",
                side_effect=pyjwt.DecodeError("bad format"),
            ),
        ):
            with pytest.raises(AuthError, match="decode"):
                await verify_token("malformed.token")


@pytest.mark.asyncio
async def test_verify_token_jwks_http_error():
    """verify_token raises AuthError when JWKS fetch fails."""
    with (
        patch(
            "ceramicraft_mcp_server.auth.jwt.get_unverified_header",
            return_value={"kid": "k1", "alg": "RS256"},
        ),
        patch("ceramicraft_mcp_server.auth._get_jwks_client") as mock_get_jwks,
    ):
        mock_jwks = AsyncMock()
        mock_jwks.get_signing_keys = AsyncMock(
            side_effect=httpx.HTTPError("connection failed")
        )
        mock_get_jwks.return_value = mock_jwks

        with pytest.raises(AuthError, match="JWKS"):
            await verify_token("any.token")
