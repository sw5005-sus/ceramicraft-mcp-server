"""Order-related MCP tools.

USER tools: create_order, list_my_orders, get_order_detail, confirm_receipt
ADMIN tools: get_order_stats, list_merchant_orders, get_merchant_order_detail, ship_order
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_admin, require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client


def _order_base() -> str:
    return f"http://{get_settings().ORDER_MS_GRPC.replace(':5001', ':8080')}"


def _prefix() -> str:
    return "/order-ms/v1"


def register_order_tools(mcp: FastMCP) -> None:
    """Register order tools on the MCP server."""

    # ─── USER ──────────────────────────────────────────────

    @mcp.tool()
    async def create_order(ctx: Context) -> dict[str, Any]:
        """Create an order from the user's cart. Requires authentication.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            Created order details including order number.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "POST",
            f"{_prefix()}/customer/orders",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def list_my_orders(
        ctx: Context,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List the authenticated user's orders.

        Args:
            ctx: MCP context (injected automatically).
            limit: Maximum number of orders to return.
            offset: Pagination offset.

        Returns:
            A dict with orders and total count.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "POST",
            f"{_prefix()}/customer/orders/list",
            user_id=user.user_id_int,
            json_body={"limit": limit, "offset": offset},
        )

    @mcp.tool()
    async def get_order_detail(ctx: Context, order_no: str) -> dict[str, Any]:
        """Get details of a specific order.

        Args:
            ctx: MCP context (injected automatically).
            order_no: The order number.

        Returns:
            Order details including items, status, and shipping info.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "GET",
            f"{_prefix()}/customer/orders/{order_no}",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def confirm_receipt(ctx: Context, order_no: str) -> dict[str, Any]:
        """Confirm receipt of an order.

        Args:
            ctx: MCP context (injected automatically).
            order_no: The order number to confirm.

        Returns:
            Confirmation result.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "PATCH",
            f"{_prefix()}/customer/orders/{order_no}/confirm",
            user_id=user.user_id_int,
        )

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def get_order_stats(ctx: Context) -> dict[str, Any]:
        """Get order statistics. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            Order statistics (total orders, revenue, etc.).
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "GET",
            f"{_prefix()}/merchant/order-stats",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def list_merchant_orders(
        ctx: Context,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all orders from merchant view. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            limit: Maximum number of orders.
            offset: Pagination offset.

        Returns:
            Orders list with merchant-specific info.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "POST",
            f"{_prefix()}/merchant/orders/list",
            user_id=user.user_id_int,
            json_body={"limit": limit, "offset": offset},
        )

    @mcp.tool()
    async def get_merchant_order_detail(
        ctx: Context,
        order_no: str,
    ) -> dict[str, Any]:
        """Get order detail from merchant view. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            order_no: The order number.

        Returns:
            Full order details including receiver info.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "GET",
            f"{_prefix()}/merchant/orders/{order_no}",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def ship_order(
        ctx: Context,
        order_no: str,
    ) -> dict[str, Any]:
        """Mark an order as shipped. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            order_no: The order number to ship.

        Returns:
            Shipping result.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _order_base(),
            "PATCH",
            f"{_prefix()}/merchant/orders/{order_no}/ship",
            user_id=user.user_id_int,
        )
