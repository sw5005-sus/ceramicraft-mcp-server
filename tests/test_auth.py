"""Tests for authentication module."""

from ceramicraft_mcp_server.auth import (
    AuthenticatedUser,
    JWKSClient,
    _extract_roles,
    _find_key,
)


def test_find_key_exists():
    jwks = {"keys": [{"kid": "abc", "kty": "RSA"}, {"kid": "xyz", "kty": "RSA"}]}
    result = _find_key(jwks, "abc")
    assert result is not None
    assert result["kid"] == "abc"


def test_find_key_missing():
    jwks = {"keys": [{"kid": "abc", "kty": "RSA"}]}
    result = _find_key(jwks, "nonexistent")
    assert result is None


def test_find_key_empty():
    assert _find_key({"keys": []}, "abc") is None
    assert _find_key({}, "abc") is None


def test_extract_roles_zitadel_format():
    payload = {
        "urn:zitadel:iam:org:project:roles": {
            "admin": {"361758611501862863": "666.us1.zitadel.cloud"},
            "user": {"361758611501862863": "666.us1.zitadel.cloud"},
        }
    }
    roles = _extract_roles(payload)
    assert "admin" in roles
    assert "user" in roles


def test_extract_roles_empty():
    assert _extract_roles({}) == []
    assert _extract_roles({"urn:zitadel:iam:org:project:roles": {}}) == []


def test_extract_roles_non_dict():
    assert _extract_roles({"urn:zitadel:iam:org:project:roles": "invalid"}) == []


def test_authenticated_user_defaults():
    user = AuthenticatedUser(user_id="123")
    assert user.user_id == "123"
    assert user.roles == []
    assert user.email == ""
    assert user.name == ""


def test_jwks_client_init():
    client = JWKSClient("https://example.com/keys")
    assert client._jwks_data is None


def test_jwks_client_invalidate():
    client = JWKSClient("https://example.com/keys")
    client._jwks_data = {"keys": []}
    client.invalidate()
    assert client._jwks_data is None
