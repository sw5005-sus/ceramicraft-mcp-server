"""Product-related MCP tools (public, no auth required)."""

from mcp.server.fastmcp import FastMCP


def register_product_tools(mcp: FastMCP) -> None:
    """Register product tools on the MCP server."""

    @mcp.tool()
    async def search_products(keyword: str, limit: int = 10) -> dict:
        """Search for ceramic products by keyword.

        Args:
            keyword: Search query string.
            limit: Maximum number of results to return (default 10).

        Returns:
            A dict with a list of matching products.
        """
        # TODO: Call product-ms gRPC SearchProducts
        return {"products": [], "total": 0, "keyword": keyword}

    @mcp.tool()
    async def get_product(product_id: int) -> dict:
        """Get detailed information about a specific product.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product details including name, description, price, and images.
        """
        # TODO: Call product-ms gRPC GetProduct
        return {"product_id": product_id, "name": "", "description": "", "price": 0}

    @mcp.tool()
    async def list_product_categories() -> dict:
        """List all available product categories.

        Returns:
            A dict with a list of categories.
        """
        # TODO: Call product-ms gRPC ListCategories
        return {"categories": []}
