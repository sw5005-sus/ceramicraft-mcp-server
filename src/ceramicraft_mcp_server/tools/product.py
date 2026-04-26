"""Product-related MCP tools.

PUBLIC tools: search_products, get_product
ADMIN tools: create_product, update_product, update_product_status,
             update_product_stock, get_merchant_product, list_merchant_products,
             get_image_upload_url
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import (
    ROLE_PRODUCT_AUDIT,
    ROLE_PRODUCT_READ,
    ROLE_PRODUCT_WRITE,
    require_role,
)
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client
from ceramicraft_mcp_server.tools.money import with_display_money_fields

PREFIX = "/product-ms/v1"
CUSTOMER_PRICE_KEYS = {"price"}


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

        result = await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/products",
            params=params,
        )
        return with_display_money_fields(result, CUSTOMER_PRICE_KEYS)

    @mcp.tool()
    async def get_product(product_id: int) -> dict[str, Any]:
        """Get detailed information about a specific product. No auth required.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product details including name, description, price, and images.
        """
        client = get_http_client()
        result = await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/product/{product_id}",
        )
        return with_display_money_fields(result, CUSTOMER_PRICE_KEYS)

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def create_product(
        ctx: Context,
        name: str,
        desc: str,
        price: int,
        category: str,
        stock: int,
        pic_info: str = "",
        material: str = "",
        dimensions: str = "",
        weight: str = "",
        capacity: str = "",
        care_instructions: str = "",
        status: int = 0,
    ) -> dict[str, Any]:
        """Create a new product listing. Requires merchant_admin or product_editor role.

        Args:
            ctx: MCP context (injected automatically).
            name: Product name.
            desc: Product description.
            price: Product price (integer, in cents).
            category: Product category.
            stock: Initial stock quantity.
            pic_info: Product image info string.
            material: Material composition.
            dimensions: Product dimensions.
            weight: Product weight.
            capacity: Product capacity (e.g. for cups/vases).
            care_instructions: Care/maintenance instructions.
            status: 0=draft, 1=published.

        Returns:
            The created product details.
        """
        user = await require_role(ctx, ROLE_PRODUCT_WRITE)
        client = get_http_client()
        body: dict[str, Any] = {
            "name": name,
            "desc": desc,
            "price": price,
            "category": category,
            "stock": stock,
            "status": status,
        }
        if pic_info:
            body["pic_info"] = pic_info
        if material:
            body["material"] = material
        if dimensions:
            body["dimensions"] = dimensions
        if weight:
            body["weight"] = weight
        if capacity:
            body["capacity"] = capacity
        if care_instructions:
            body["care_instructions"] = care_instructions

        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "POST",
            f"{PREFIX}/merchant/products",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def update_product(
        ctx: Context,
        product_id: int,
        name: str | None = None,
        desc: str | None = None,
        price: int | None = None,
        category: str | None = None,
        pic_info: str | None = None,
        material: str | None = None,
        dimensions: str | None = None,
        weight: str | None = None,
        capacity: str | None = None,
        care_instructions: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing product. Requires merchant_admin or product_editor role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID to update.
            name: New product name.
            desc: New product description.
            price: New price (integer, in cents).
            category: New category.
            pic_info: New image info string.
            material: New material.
            dimensions: New dimensions.
            weight: New weight.
            capacity: New capacity.
            care_instructions: New care instructions.

        Returns:
            Updated product details.
        """
        user = await require_role(ctx, ROLE_PRODUCT_WRITE)
        client = get_http_client()
        body: dict[str, Any] = {"id": product_id}
        if name is not None:
            body["name"] = name
        if desc is not None:
            body["desc"] = desc
        if price is not None:
            body["price"] = price
        if category is not None:
            body["category"] = category
        if pic_info is not None:
            body["pic_info"] = pic_info
        if material is not None:
            body["material"] = material
        if dimensions is not None:
            body["dimensions"] = dimensions
        if weight is not None:
            body["weight"] = weight
        if capacity is not None:
            body["capacity"] = capacity
        if care_instructions is not None:
            body["care_instructions"] = care_instructions

        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "PUT",
            f"{PREFIX}/merchant/products/{product_id}",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def update_product_status(
        ctx: Context,
        product_id: int,
        status: int,
    ) -> dict[str, Any]:
        """Update product publish status. Requires merchant_admin or product_auditor role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID.
            status: New status: 0=unpublished, 1=published.

        Returns:
            Update result.
        """
        user = await require_role(ctx, ROLE_PRODUCT_AUDIT)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "PATCH",
            f"{PREFIX}/merchant/products/{product_id}/status",
            user_id=user.user_id_int,
            json_body={"status": status},
        )

    @mcp.tool()
    async def update_product_stock(
        ctx: Context,
        product_id: int,
        stock: int,
    ) -> dict[str, Any]:
        """Update product stock quantity. Requires merchant_admin or product_editor role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID.
            stock: New stock quantity.

        Returns:
            Update result.
        """
        user = await require_role(ctx, ROLE_PRODUCT_WRITE)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "PATCH",
            f"{PREFIX}/merchant/products/{product_id}/stock",
            user_id=user.user_id_int,
            json_body={"stock": stock},
        )

    @mcp.tool()
    async def get_merchant_product(
        ctx: Context,
        product_id: int,
    ) -> dict[str, Any]:
        """Get product detail from merchant view. Requires merchant_admin, product_editor, or product_auditor role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID.

        Returns:
            Full product details including internal merchant fields.
        """
        user = await require_role(ctx, ROLE_PRODUCT_READ)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "GET",
            f"{PREFIX}/merchant/product/{product_id}",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def list_merchant_products(
        ctx: Context,
        keyword: str = "",
        category: str = "",
        offset: int = 0,
        order_by: int = 0,
    ) -> dict[str, Any]:
        """List products from merchant view. Requires merchant_admin, product_editor, or product_auditor role.

        Args:
            ctx: MCP context (injected automatically).
            keyword: Search keyword.
            category: Filter by category.
            offset: Pagination offset.
            order_by: Sort order: 0=newest first, 1=oldest first.

        Returns:
            Product list with merchant-specific fields.
        """
        user = await require_role(ctx, ROLE_PRODUCT_READ)
        client = get_http_client()
        params: dict[str, Any] = {"offset": offset, "order_by": order_by}
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category

        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "GET",
            f"{PREFIX}/merchant/products",
            user_id=user.user_id_int,
            params=params,
        )

    @mcp.tool()
    async def get_image_upload_url(
        ctx: Context,
        image_type: str = "jpg",
    ) -> dict[str, Any]:
        """Get a presigned URL for product image upload. Requires merchant_admin or product_editor role.

        Args:
            ctx: MCP context (injected automatically).
            image_type: Image format: jpg, png, or jpeg.

        Returns:
            Presigned upload URL.
        """
        user = await require_role(ctx, ROLE_PRODUCT_WRITE)
        client = get_http_client()
        return await client.call(
            get_settings().PRODUCT_MS_HTTP,
            "POST",
            f"{PREFIX}/merchant/images/upload-urls",
            user_id=user.user_id_int,
            json_body={"image_type": image_type},
        )
