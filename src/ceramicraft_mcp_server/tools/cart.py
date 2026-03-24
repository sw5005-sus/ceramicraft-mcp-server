"""Cart-related MCP tools (all require USER auth)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client


def _product_base() -> str:
    return f"http://{get_settings().PRODUCT_MS_GRPC.replace(':5001', ':8080')}"


def _prefix() -> str:
    return "/product-ms/v1"


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
            _product_base(),
            "GET",
            f"{_prefix()}/customer/cart",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def add_to_cart(
        ctx: Context,
        product_id: int,
        quantity: int = 1,
    ) -> dict[str, Any]:
        """Add an item to the user's cart.

        Args:
            ctx: MCP context (injected automatically).
            product_id: Product to add.
            quantity: How many to add (default 1).

        Returns:
            Created cart item details.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _product_base(),
            "POST",
            f"{_prefix()}/customer/cart/items",
            user_id=user.user_id_int,
            json_body={"product_id": product_id, "quantity": quantity},
        )

    @mcp.tool()
    async def update_cart_item(
        ctx: Context,
        item_id: int,
        quantity: int,
    ) -> dict[str, Any]:
        """Update quantity of a cart item.

        Args:
            ctx: MCP context (injected automatically).
            item_id: Cart item ID to update.
            quantity: New quantity.

        Returns:
            Updated cart item.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _product_base(),
            "PUT",
            f"{_prefix()}/customer/cart/items/{item_id}",
            user_id=user.user_id_int,
            json_body={"quantity": quantity},
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
            _product_base(),
            "DELETE",
            f"{_prefix()}/customer/cart/items/{item_id}",
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
            _product_base(),
            "GET",
            f"{_prefix()}/customer/cart/price-estimate",
            user_id=user.user_id_int,
        )
