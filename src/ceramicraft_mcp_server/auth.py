"""Authentication and authorization utilities."""

from dataclasses import dataclass

from mcp.server.auth.provider import AccessToken, TokenVerifier


@dataclass
class UserInfo:
    """Authenticated user information extracted from token."""

    user_id: str
    roles: list[str]


class ZitadelTokenVerifier(TokenVerifier):
    """Verify JWT tokens issued by Zitadel.

    TODO: Implement actual JWT verification against Zitadel JWKS endpoint.
    For now, this is a placeholder that accepts all tokens.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        # TODO: Decode and verify JWT, extract user info
        # 1. Fetch JWKS from Zitadel
        # 2. Verify signature, expiry, issuer
        # 3. Extract user_id and roles from claims
        # 4. Return AccessToken with scopes
        return AccessToken(
            token=token,
            client_id="unknown",
            scopes=["user"],
        )
