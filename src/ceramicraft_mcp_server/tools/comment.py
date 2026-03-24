"""Comment-related MCP tools (mixed: read=public, write=auth required)."""

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError


def register_comment_tools(mcp: FastMCP) -> None:
    """Register comment tools on the MCP server."""

    @mcp.tool()
    async def list_comments(product_id: int, limit: int = 20, offset: int = 0) -> dict:
        """List comments for a product (public, no auth required).

        Args:
            product_id: The product to get comments for.
            limit: Maximum number of comments to return.
            offset: Pagination offset.

        Returns:
            A dict with comments and total count.
        """
        # TODO: Call comment-ms gRPC ListComments
        return {"comments": [], "total": 0, "product_id": product_id}

    @mcp.tool()
    async def add_comment(
        ctx: Context,
        product_id: int,
        content: str,
        rating: int,
    ) -> dict:
        """Add a comment to a product (requires authentication).

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product to comment on.
            content: Comment text.
            rating: Rating score (1-5).

        Returns:
            The created comment.
        """
        # TODO: Extract user_id from ctx token
        # user_id = require_auth(ctx)
        _ = ctx  # placeholder
        if not 1 <= rating <= 5:
            raise ToolError("Rating must be between 1 and 5")
        # TODO: Call comment-ms gRPC AddComment
        return {"comment_id": "", "product_id": product_id, "content": content, "rating": rating}
