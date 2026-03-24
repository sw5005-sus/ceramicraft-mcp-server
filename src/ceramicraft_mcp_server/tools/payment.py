"""Payment-related MCP tools.

USER tools: get_pay_account, top_up_account
ADMIN tools: list_redeem_codes, generate_redeem_codes
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_admin, require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client


def _payment_base() -> str:
    return f"http://{get_settings().PAYMENT_MS_GRPC.replace(':5001', ':8080')}"


def _prefix() -> str:
    return "/payment-ms/v1"


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
            _payment_base(),
            "GET",
            f"{_prefix()}/customer/pay-accounts/self",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def top_up_account(
        ctx: Context,
        amount: float,
        redeem_code: str = "",
    ) -> dict[str, Any]:
        """Top up the user's payment account.

        Args:
            ctx: MCP context (injected automatically).
            amount: Amount to top up.
            redeem_code: Optional redeem code to apply.

        Returns:
            Top-up result including new balance.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {"amount": amount}
        if redeem_code:
            body["redeem_code"] = redeem_code

        return await client.call(
            _payment_base(),
            "POST",
            f"{_prefix()}/customer/pay-accounts/self/top-ups",
            user_id=user.user_id_int,
            json_body=body,
        )

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def list_redeem_codes(ctx: Context) -> dict[str, Any]:
        """List all redeem codes. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            List of redeem codes with details.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _payment_base(),
            "GET",
            f"{_prefix()}/merchant/redeem-codes",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def generate_redeem_codes(
        ctx: Context,
        count: int = 1,
        amount: float = 0,
    ) -> dict[str, Any]:
        """Generate new redeem codes. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            count: Number of codes to generate.
            amount: Value of each redeem code.

        Returns:
            Generated redeem codes.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _payment_base(),
            "POST",
            f"{_prefix()}/merchant/redeem-codes/generate",
            user_id=user.user_id_int,
            json_body={"count": count, "amount": amount},
        )
