"""Order-related MCP tools.

USER tools: create_order, list_my_orders, get_order_detail, confirm_receipt
ADMIN tools: get_order_stats, list_merchant_orders, get_merchant_order_detail, ship_order
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import ROLE_MERCHANT_ADMIN, require_role, require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client
from ceramicraft_mcp_server.tools.money import with_display_money_fields

PREFIX = "/order-ms/v1"
USER_ORDER_PRICE_KEYS = {"pay_amount", "price", "total_amount", "total_price"}


def register_order_tools(mcp: FastMCP) -> None:
    """Register order tools on the MCP server."""

    # ─── USER ──────────────────────────────────────────────

    @mcp.tool()
    async def create_order(
        ctx: Context,
        receiver_first_name: str,
        receiver_last_name: str,
        receiver_phone: str,
        receiver_address: str,
        receiver_country: str,
        receiver_zip_code: int,
        remark: str = "",
    ) -> dict[str, Any]:
        """Create an order. Requires authentication.

        The order items come from the user's selected cart items.

        Args:
            ctx: MCP context (injected automatically).
            receiver_first_name: Receiver's first name.
            receiver_last_name: Receiver's last name.
            receiver_phone: Receiver's phone number.
            receiver_address: Receiver's address.
            receiver_country: Receiver's country.
            receiver_zip_code: Receiver's postal code.
            remark: Order remark/notes.

        Returns:
            Created order details including order number.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {
            "receiver_first_name": receiver_first_name,
            "receiver_last_name": receiver_last_name,
            "receiver_phone": receiver_phone,
            "receiver_address": receiver_address,
            "receiver_country": receiver_country,
            "receiver_zip_code": receiver_zip_code,
        }
        if remark:
            body["remark"] = remark

        result = await client.call(
            get_settings().ORDER_MS_HTTP,
            "POST",
            f"{PREFIX}/customer/orders",
            user_id=user.user_id_int,
            json_body=body,
        )
        return with_display_money_fields(result, USER_ORDER_PRICE_KEYS)

    @mcp.tool()
    async def list_my_orders(
        ctx: Context,
        limit: int = 20,
        offset: int = 0,
        start_time: str = "",
        end_time: str = "",
    ) -> dict[str, Any]:
        """List the authenticated user's orders.

        Args:
            ctx: MCP context (injected automatically).
            limit: Maximum number of orders to return.
            offset: Pagination offset.
            start_time: Filter orders created after this time (ISO 8601).
            end_time: Filter orders created before this time (ISO 8601).

        Returns:
            A dict with orders and total count.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {"limit": limit, "offset": offset}
        if start_time:
            body["start_time"] = start_time
        if end_time:
            body["end_time"] = end_time

        result = await client.call(
            get_settings().ORDER_MS_HTTP,
            "POST",
            f"{PREFIX}/customer/orders/list",
            user_id=user.user_id_int,
            json_body=body,
        )
        return with_display_money_fields(result, USER_ORDER_PRICE_KEYS)

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
        result = await client.call(
            get_settings().ORDER_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/orders/{order_no}",
            user_id=user.user_id_int,
        )
        return with_display_money_fields(result, USER_ORDER_PRICE_KEYS)

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
            get_settings().ORDER_MS_HTTP,
            "PATCH",
            f"{PREFIX}/customer/orders/{order_no}/confirm",
            user_id=user.user_id_int,
            json_body={"order_no": order_no},
        )

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def get_order_stats(ctx: Context) -> dict[str, Any]:
        """Get order statistics. Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            Order statistics (total orders, revenue, etc.).
        """
        user = await require_role(ctx, ROLE_MERCHANT_ADMIN)
        client = get_http_client()
        return await client.call(
            get_settings().ORDER_MS_HTTP,
            "GET",
            f"{PREFIX}/merchant/order-stats",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def list_merchant_orders(
        ctx: Context,
        limit: int = 20,
        offset: int = 0,
        order_no: str = "",
        order_status: int | None = None,
        user_id: int | None = None,
        start_time: str = "",
        end_time: str = "",
    ) -> dict[str, Any]:
        """List all orders from merchant view. Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).
            limit: Maximum number of orders.
            offset: Pagination offset.
            order_no: Filter by order number.
            order_status: Filter by order status.
            user_id: Filter by customer user ID.
            start_time: Filter by creation time start (ISO 8601).
            end_time: Filter by creation time end (ISO 8601).

        Returns:
            Orders list with merchant-specific info.
        """
        admin = await require_role(ctx, ROLE_MERCHANT_ADMIN)
        client = get_http_client()
        body: dict[str, Any] = {"limit": limit, "offset": offset}
        if order_no:
            body["order_no"] = order_no
        if order_status is not None:
            body["order_status"] = order_status
        if user_id is not None:
            body["user_id"] = user_id
        if start_time:
            body["start_time"] = start_time
        if end_time:
            body["end_time"] = end_time

        return await client.call(
            get_settings().ORDER_MS_HTTP,
            "POST",
            f"{PREFIX}/merchant/orders/list",
            user_id=admin.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def get_merchant_order_detail(
        ctx: Context,
        order_no: str,
    ) -> dict[str, Any]:
        """Get order detail from merchant view. Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).
            order_no: The order number.

        Returns:
            Full order details including receiver info.
        """
        user = await require_role(ctx, ROLE_MERCHANT_ADMIN)
        client = get_http_client()
        return await client.call(
            get_settings().ORDER_MS_HTTP,
            "GET",
            f"{PREFIX}/merchant/orders/{order_no}",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def ship_order(
        ctx: Context,
        order_no: str,
        tracking_no: str,
    ) -> dict[str, Any]:
        """Mark an order as shipped. Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).
            order_no: The order number to ship.
            tracking_no: Shipping tracking number.

        Returns:
            Shipping result.
        """
        user = await require_role(ctx, ROLE_MERCHANT_ADMIN)
        client = get_http_client()
        return await client.call(
            get_settings().ORDER_MS_HTTP,
            "PATCH",
            f"{PREFIX}/merchant/orders/{order_no}/ship",
            user_id=user.user_id_int,
            json_body={"tracking_no": tracking_no},
        )
