"""Product-related MCP tools.

PUBLIC tools: search_products, get_product, list_product_categories
ADMIN tools: create_product, update_product, update_product_status,
             update_product_stock, get_merchant_product, list_merchant_products,
             get_image_upload_url
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_admin
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client


def _product_base() -> str:
    return f"http://{get_settings().PRODUCT_MS_GRPC.replace(':5001', ':8080')}"


def _prefix() -> str:
    return "/product-ms/v1"


def register_product_tools(mcp: FastMCP) -> None:
    """Register product tools on the MCP server."""

    # ─── PUBLIC ─────────────────────────────────────────────

    @mcp.tool()
    async def search_products(
        keyword: str = "",
        category: str = "",
        offset: int = 0,
        order_by: int = 0,
    ) -> dict[str, Any]:
        """Search for ceramic products. No authentication required.

        Args:
            keyword: Search query string.
            category: Filter by product category.
            offset: Pagination offset (default 0).
            order_by: Sort order: 0=newest first, 1=oldest first.

        Returns:
            A dict with a list of matching products.
        """
        client = get_http_client()
        params: dict[str, Any] = {"offset": offset, "order_by": order_by}
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category

        return await client.call(
            _product_base(),
            "GET",
            f"{_prefix()}/customer/products",
            params=params,
        )

    @mcp.tool()
    async def get_product(product_id: int) -> dict[str, Any]:
        """Get detailed information about a specific product. No auth required.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product details including name, description, price, and images.
        """
        client = get_http_client()
        return await client.call(
            _product_base(),
            "GET",
            f"{_prefix()}/customer/product/{product_id}",
        )

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def create_product(
        ctx: Context,
        name: str,
        description: str,
        price: float,
        category: str,
        stock: int,
        images: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new product listing. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            name: Product name.
            description: Product description.
            price: Product price.
            category: Product category.
            stock: Initial stock quantity.
            images: List of image URLs.

        Returns:
            The created product details.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        body: dict[str, Any] = {
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "stock": stock,
        }
        if images:
            body["images"] = images

        return await client.call(
            _product_base(),
            "POST",
            f"{_prefix()}/merchant/products",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def update_product(
        ctx: Context,
        product_id: int,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing product. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID to update.
            name: New product name.
            description: New product description.
            price: New price.
            category: New category.

        Returns:
            Updated product details.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if price is not None:
            body["price"] = price
        if category is not None:
            body["category"] = category

        return await client.call(
            _product_base(),
            "PUT",
            f"{_prefix()}/merchant/products/{product_id}",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def update_product_status(
        ctx: Context,
        product_id: int,
        status: str,
    ) -> dict[str, Any]:
        """Update product publish status. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID.
            status: New status (e.g. "published", "draft").

        Returns:
            Update result.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _product_base(),
            "PATCH",
            f"{_prefix()}/merchant/products/{product_id}/status",
            user_id=user.user_id_int,
            json_body={"status": status},
        )

    @mcp.tool()
    async def update_product_stock(
        ctx: Context,
        product_id: int,
        stock: int,
    ) -> dict[str, Any]:
        """Update product stock quantity. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID.
            stock: New stock quantity.

        Returns:
            Update result.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _product_base(),
            "PATCH",
            f"{_prefix()}/merchant/products/{product_id}/stock",
            user_id=user.user_id_int,
            json_body={"stock": stock},
        )

    @mcp.tool()
    async def get_merchant_product(
        ctx: Context,
        product_id: int,
    ) -> dict[str, Any]:
        """Get product detail from merchant view. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID.

        Returns:
            Full product details including internal merchant fields.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _product_base(),
            "GET",
            f"{_prefix()}/merchant/product/{product_id}",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def list_merchant_products(
        ctx: Context,
        keyword: str = "",
        category: str = "",
        offset: int = 0,
    ) -> dict[str, Any]:
        """List products from merchant view. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            keyword: Search keyword.
            category: Filter by category.
            offset: Pagination offset.

        Returns:
            Product list with merchant-specific fields.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        params: dict[str, Any] = {"offset": offset}
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category

        return await client.call(
            _product_base(),
            "GET",
            f"{_prefix()}/merchant/products",
            user_id=user.user_id_int,
            params=params,
        )

    @mcp.tool()
    async def get_image_upload_url(
        ctx: Context,
        file_names: list[str],
    ) -> dict[str, Any]:
        """Get presigned URLs for product image upload. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            file_names: List of file names to upload.

        Returns:
            Presigned upload URLs.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            _product_base(),
            "POST",
            f"{_prefix()}/merchant/images/upload-urls",
            user_id=user.user_id_int,
            json_body={"file_names": file_names},
        )
