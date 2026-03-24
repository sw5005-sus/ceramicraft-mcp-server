"""Comment/Review-related MCP tools.

PUBLIC tools: list_product_reviews
USER tools: get_user_reviews, create_review, like_review
ADMIN tools: list_reviews_admin, delete_review, pin_review, reply_to_review
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from ceramicraft_mcp_server.auth import require_admin, require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client

PREFIX = "/comment-ms/v1"


def register_comment_tools(mcp: FastMCP) -> None:
    """Register comment tools on the MCP server."""

    # ─── PUBLIC ─────────────────────────────────────────────

    @mcp.tool()
    async def list_product_reviews(product_id: int) -> dict[str, Any]:
        """List reviews for a product. No authentication required.

        Args:
            product_id: The product ID to get reviews for.

        Returns:
            A dict with reviews for the product.
        """
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/reviews/product/{product_id}",
        )

    # ─── USER ──────────────────────────────────────────────

    @mcp.tool()
    async def get_user_reviews(ctx: Context) -> dict[str, Any]:
        """Get the authenticated user's own reviews.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            A dict with the user's reviews.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/reviews/user",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def create_review(
        ctx: Context,
        product_id: int,
        content: str,
        stars: int,
        is_anonymous: bool = False,
        pic_info: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a review for a product. Requires authentication.

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product to review.
            content: Review text content.
            stars: Rating score (1-5).
            is_anonymous: Whether to post anonymously.
            pic_info: List of image URLs to attach.

        Returns:
            The created review.
        """
        if not 1 <= stars <= 5:
            raise ToolError("Stars must be between 1 and 5")

        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {
            "productID": product_id,
            "content": content,
            "stars": stars,
            "is_anonymous": is_anonymous,
        }
        if pic_info:
            body["pic_info"] = pic_info

        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/customer/reviews",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def like_review(ctx: Context, review_id: str) -> dict[str, Any]:
        """Like a review. Requires authentication.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to like.

        Returns:
            Like result.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/customer/reviews/{review_id}/like",
            user_id=user.user_id_int,
            json_body={"review_id": review_id},
        )

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def list_reviews_admin(
        ctx: Context,
        product_id: int,
        stars: int = 0,
    ) -> dict[str, Any]:
        """List reviews for moderation. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: Filter by product ID.
            stars: Filter by star rating (0 = any).

        Returns:
            Reviews list for moderation.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/merchant/reviews/list",
            user_id=user.user_id_int,
            json_body={"product_id": product_id, "stars": stars},
        )

    @mcp.tool()
    async def delete_review(ctx: Context, review_id: str) -> dict[str, Any]:
        """Delete a review (moderation). Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to delete.

        Returns:
            Deletion result.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "DELETE",
            f"{PREFIX}/merchant/reviews/{review_id}",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def pin_review(
        ctx: Context,
        review_id: str,
        is_pinned: bool = True,
    ) -> dict[str, Any]:
        """Pin or unpin a review. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to pin/unpin.
            is_pinned: True to pin, False to unpin.

        Returns:
            Pin result.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "PATCH",
            f"{PREFIX}/merchant/reviews/{review_id}",
            user_id=user.user_id_int,
            json_body={"is_pinned": is_pinned},
        )

    @mcp.tool()
    async def reply_to_review(
        ctx: Context,
        review_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Reply to a review as merchant. Requires admin/merchant role.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to reply to.
            content: Reply text content.

        Returns:
            The created reply.
        """
        user = await require_admin(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/merchant/reviews/{review_id}/replies",
            user_id=user.user_id_int,
            json_body={"content": content, "parentID": review_id},
        )
