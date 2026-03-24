"""Order-related MCP tools (all require authentication)."""

from mcp.server.fastmcp import Context, FastMCP


def register_order_tools(mcp: FastMCP) -> None:
    """Register order tools on the MCP server."""

    @mcp.tool()
    async def list_my_orders(ctx: Context, limit: int = 20, offset: int = 0) -> dict:
        """List the authenticated user's orders.

        Args:
            ctx: MCP context (injected automatically).
            limit: Maximum number of orders to return.
            offset: Pagination offset.

        Returns:
            A dict with orders and total count.
        """
        # TODO: Extract user_id from ctx, call order-ms gRPC
        _ = ctx
        return {"orders": [], "total": 0}

    @mcp.tool()
    async def get_order_detail(ctx: Context, order_no: str) -> dict:
        """Get details of a specific order.

        Args:
            ctx: MCP context (injected automatically).
            order_no: The order number.

        Returns:
            Order details including items, status, and shipping info.
        """
        # TODO: Extract user_id from ctx, call order-ms gRPC
        _ = ctx
        return {"order_no": order_no, "status": "", "items": []}
