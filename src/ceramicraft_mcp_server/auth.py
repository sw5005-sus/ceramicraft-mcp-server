"""Authentication and authorization utilities.

Verifies Zitadel-issued JWT tokens using JWKS public keys.
Provides helpers for MCP tool auth enforcement.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
import jwt
import jwt.algorithms
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from ceramicraft_mcp_server.config import get_settings

logger = logging.getLogger(__name__)

# Admin roles that grant elevated access
ADMIN_ROLES = frozenset({"merchant_admin", "product_auditor", "product_editor"})

# Per-tool role sets
ROLE_MERCHANT_ADMIN = frozenset({"merchant_admin"})
ROLE_PRODUCT_WRITE = frozenset({"merchant_admin", "product_editor"})
ROLE_PRODUCT_READ = frozenset({"merchant_admin", "product_editor", "product_auditor"})
ROLE_PRODUCT_AUDIT = frozenset({"merchant_admin", "product_auditor"})


@dataclass
class AuthenticatedUser:
    """Authenticated user information extracted from a verified JWT."""

    user_id: str
    roles: list[str] = field(default_factory=list)
    email: str = ""
    name: str = ""

    @property
    def is_admin(self) -> bool:
        """Check if user has any admin role."""
        return bool(ADMIN_ROLES & set(self.roles))

    @property
    def user_id_int(self) -> int:
        """Return user_id as integer for X-Original-User-ID header."""
        try:
            return int(self.user_id)
        except (ValueError, TypeError):
            return 0


class AuthError(Exception):
    """Raised when authentication fails."""


class JWKSClient:
    """Fetches and caches JWKS public keys from Zitadel."""

    def __init__(self, jwks_url: str) -> None:
        self._jwks_url = jwks_url
        self._jwks_data: dict[str, Any] | None = None

    async def get_signing_keys(self) -> dict[str, Any]:
        """Fetch JWKS keys, caching the result."""
        if self._jwks_data is None:
            await self._refresh()
        assert self._jwks_data is not None
        return self._jwks_data

    async def _refresh(self) -> None:
        """Fetch fresh JWKS data from the endpoint."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(self._jwks_url, timeout=10)
            resp.raise_for_status()
            self._jwks_data = resp.json()

    def invalidate(self) -> None:
        """Clear cached keys (call on verification failure to retry)."""
        self._jwks_data = None


# Module-level singleton
_jwks_client: JWKSClient | None = None


def _get_jwks_client() -> JWKSClient:
    global _jwks_client
    if _jwks_client is None:
        settings = get_settings()
        _jwks_client = JWKSClient(settings.MCP_ZITADEL_JWKS_URL)
    return _jwks_client


def _extract_bearer_token(ctx: Context) -> str | None:
    """Extract Bearer token from MCP request context.

    MCP Streamable HTTP transport passes the Authorization header
    through the request context.
    """
    # FastMCP stores request headers in the context session
    # Try to get from transport headers
    headers = getattr(ctx, "headers", None)
    if headers:
        auth_header = headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

    # Fallback: check meta/extra from context
    meta = getattr(ctx, "meta", None)
    if meta:
        extra = getattr(meta, "extra", None)
        if isinstance(extra, dict):
            token = extra.get("token") or extra.get("authorization", "")
            if isinstance(token, str):
                if token.startswith("Bearer "):
                    return token[7:]
                if token:
                    return token

    return None


async def require_user(ctx: Context) -> AuthenticatedUser:
    """Extract and verify user from MCP context. Raises ToolError on failure.

    Use this in USER-level tools that need a valid authenticated user.
    """
    token = _extract_bearer_token(ctx)
    if not token:
        raise ToolError("Authentication required. Please provide a valid Bearer token.")

    try:
        return await verify_token(token)
    except AuthError as e:
        raise ToolError(f"Authentication failed: {e}")


async def require_admin(ctx: Context) -> AuthenticatedUser:
    """Extract and verify admin user from MCP context. Raises ToolError on failure.

    Accepts any ADMIN_ROLES role. For fine-grained control, use require_role().
    """
    return await require_role(ctx, ADMIN_ROLES)


async def require_role(
    ctx: Context, allowed_roles: frozenset[str]
) -> AuthenticatedUser:
    """Extract and verify user has one of the allowed roles.

    Args:
        ctx: MCP request context.
        allowed_roles: Set of role names that grant access.

    Raises:
        ToolError: If user is not authenticated or lacks required role.
    """
    user = await require_user(ctx)
    if not (set(user.roles) & allowed_roles):
        roles_str = ", ".join(sorted(allowed_roles))
        raise ToolError(f"Access denied. Required role: {roles_str}.")
    return user


async def verify_token(token: str) -> AuthenticatedUser:
    """Verify a Zitadel JWT and extract user information.

    Args:
        token: The raw JWT string (without 'Bearer ' prefix).

    Returns:
        AuthenticatedUser with extracted claims.

    Raises:
        AuthError: If the token is invalid, expired, or unverifiable.
    """
    settings = get_settings()
    jwks_client = _get_jwks_client()

    try:
        # Read kid from header (unverified) to look up the correct JWKS key.
        # The actual signature verification happens in jwt.decode() below.
        unverified_header = jwt.get_unverified_header(token)  # NOSONAR
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "RS256")

        if not kid:
            raise AuthError("Token header missing 'kid'")

        # Get JWKS and find matching key
        jwks_data = await jwks_client.get_signing_keys()
        key_data = _find_key(jwks_data, kid)

        if key_data is None:
            # Key not found — maybe rotated. Refresh and retry once.
            jwks_client.invalidate()
            jwks_data = await jwks_client.get_signing_keys()
            key_data = _find_key(jwks_data, kid)

        if key_data is None:
            raise AuthError(f"No matching key found for kid={kid}")

        # Build the public key from JWK
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

        # Verify and decode — from_jwk returns RSAPrivateKey | RSAPublicKey,
        # but JWK public keys always yield RSAPublicKey.
        payload = jwt.decode(
            token,
            public_key,  # type: ignore[arg-type]
            algorithms=[alg],
            issuer=settings.MCP_ZITADEL_ISSUER,
            options={"verify_aud": False},  # MCP tokens may not have audience
        )

        # Extract user info from Zitadel claims
        user_id = payload.get("sub", "")
        roles = _extract_roles(payload)
        email = payload.get("email", "")
        name = payload.get("name", payload.get("preferred_username", ""))

        return AuthenticatedUser(
            user_id=user_id,
            roles=roles,
            email=email,
            name=name,
        )

    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidIssuerError:
        raise AuthError("Invalid token issuer")
    except jwt.DecodeError as e:
        raise AuthError(f"Failed to decode token: {e}")
    except jwt.PyJWTError as e:
        raise AuthError(f"Token verification failed: {e}")
    except httpx.HTTPError as e:
        raise AuthError(f"Failed to fetch JWKS: {e}")


def _find_key(jwks_data: dict[str, Any], kid: str) -> dict[str, Any] | None:
    """Find a key in JWKS data by key ID."""
    for key in jwks_data.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


def _extract_roles(payload: dict[str, Any]) -> list[str]:
    """Extract roles from Zitadel token claims.

    Zitadel puts roles in `urn:zitadel:iam:org:project:roles` claim
    as a dict like {"merchant_admin": {"orgId": "..."}, "product_editor": {"orgId": "..."}}.
    """
    roles_claim = payload.get("urn:zitadel:iam:org:project:roles", {})
    if isinstance(roles_claim, dict):
        return [str(k) for k in roles_claim.keys()]
    return []
