"""Cart-related MCP tools (all require USER auth).

All cart endpoints are under product-ms.
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client

PREFIX = "/product-ms/v1"


def register_cart_tools(mcp: FastMCP) -> None:
    """Register cart tools on the MCP server."""

    @mcp.tool()
    async def get_cart(ctx: Context) -> dict[str, Any]:
        """Get the authenticated user's shopping cart.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            Cart contents including items and quantities.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/cart",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def add_to_cart(
        ctx: Context,
        product_id: int,
        quantity: int = 1,
        selected: bool = True,
    ) -> dict[str, Any]:
        """Add an item to the user's cart.

        Args:
            ctx: MCP context (injected automatically).
            product_id: Product to add.
            quantity: How many to add (minimum 1).
            selected: Whether the item is selected for checkout.

        Returns:
            Created cart item details.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "POST",
            f"{PREFIX}/customer/cart/items",
            user_id=user.user_id_int,
            json_body={
                "product_id": product_id,
                "quantity": quantity,
                "selected": selected,
            },
        )

    @mcp.tool()
    async def update_cart_item(
        ctx: Context,
        item_id: int,
        product_id: int,
        quantity: int = 1,
        selected: bool = True,
    ) -> dict[str, Any]:
        """Update a cart item (quantity or selection).

        Args:
            ctx: MCP context (injected automatically).
            item_id: Cart item ID to update.
            product_id: Product ID.
            quantity: New quantity (minimum 1).
            selected: Whether the item is selected for checkout.

        Returns:
            Updated cart item.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "PUT",
            f"{PREFIX}/customer/cart/items/{item_id}",
            user_id=user.user_id_int,
            json_body={
                "product_id": product_id,
                "quantity": quantity,
                "selected": selected,
            },
        )

    @mcp.tool()
    async def remove_cart_item(
        ctx: Context,
        item_id: int,
    ) -> dict[str, Any]:
        """Remove an item from the cart.

        Args:
            ctx: MCP context (injected automatically).
            item_id: Cart item ID to remove.

        Returns:
            Deletion result.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "DELETE",
            f"{PREFIX}/customer/cart/items/{item_id}",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def estimate_cart_price(ctx: Context) -> dict[str, Any]:
        """Calculate estimated order price from selected cart items.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            Price estimation details.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/cart/price-estimate",
            user_id=user.user_id_int,
        )
