"""Payment-related MCP tools.

USER tools: get_pay_account, top_up_account
ADMIN tools: list_redeem_codes, generate_redeem_codes
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_admin, require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client

PREFIX = "/payment-ms/v1"


def register_payment_tools(mcp: FastMCP) -> None:
    """Register payment tools on the MCP server."""

    # ─── USER ──────────────────────────────────────────────

    @mcp.tool()
    async def get_pay_account(ctx: Context) -> dict[str, Any]:
        """Get the authenticated user's payment account and balance.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            Payment account details including balance.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PAYMENT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/pay-accounts/self",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def top_up_account(
        ctx: Context,
        redeem_code: str,
    ) -> dict[str, Any]:
        """Top up the user's payment account using a redeem code.

        Args:
            ctx: MCP context (injected automatically).
            redeem_code: The redeem code to apply.

        Returns:
            Top-up result including new balance.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PAYMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/customer/pay-accounts/self/top-ups",
            user_id=user.user_id_int,
            json_body={"redeem_code": redeem_code},
        )

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def list_redeem_codes(
        ctx: Context,
        code: str = "",
        limit: int = 20,
        used: bool | None = None,
    ) -> dict[str, Any]:
        """List redeem codes. Requires ADMIN role.

        Args:
            ctx: MCP context (injected automatically).
            code: Filter by specific code.
            limit: Maximum number of codes to return.
            used: Filter by usage status (True=used, False=unused, None=all).

        Returns:
            List of redeem codes with details.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        params: dict[str, Any] = {"limit": limit}
        if code:
            params["code"] = code
        if used is not None:
            params["used"] = used

        return await client.call(
            get_settings().PAYMENT_MS_HTTP,
            "GET",
            f"{PREFIX}/merchant/redeem-codes",
            user_id=user.user_id_int,
            params=params,
        )

    @mcp.tool()
    async def generate_redeem_codes(
        ctx: Context,
        amount: int,
        count: int = 1,
    ) -> dict[str, Any]:
        """Generate new redeem codes. Requires ADMIN role.

        Args:
            ctx: MCP context (injected automatically).
            amount: Value of each redeem code (integer).
            count: Number of codes to generate.

        Returns:
            Generated redeem codes.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PAYMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/merchant/redeem-codes/generate",
            user_id=user.user_id_int,
            params={"amount": amount, "count": count},
        )
