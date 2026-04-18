"""Comment/Review-related MCP tools.

USER tools: list_product_reviews, get_user_reviews, create_review, like_review
PUBLIC tools: list_reviews_by_user_id
ADMIN tools: list_reviews_admin, delete_review, pin_review, reply_to_review
AGENT tools: list_reviews_by_status, update_review_status
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from ceramicraft_mcp_server.auth import ROLE_MERCHANT_ADMIN, require_role, require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client

PREFIX = "/v1"


def register_comment_tools(mcp: FastMCP) -> None:
    """Register comment tools on the MCP server."""

    # ─── USER ──────────────────────────────────────────────

    @mcp.tool()
    async def list_product_reviews(ctx: Context, product_id: int) -> dict[str, Any]:
        """List reviews for a product. Requires authentication.

        Note: comment-ms requires auth even for product review listing
        (the endpoint is behind AuthMiddleware).

        Args:
            ctx: MCP context (injected automatically).
            product_id: The product ID to get reviews for.

        Returns:
            A dict with reviews for the product.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "GET",
            f"{PREFIX}/customer/reviews/product/{product_id}",
            user_id=user.user_id_int,
        )

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

    # ─── PUBLIC ────────────────────────────────────────────

    @mcp.tool()
    async def list_reviews_by_user_id(user_id: int) -> dict[str, Any]:
        """Get all non-rejected reviews submitted by a specific user. No authentication required.

        Results are sorted by created_at descending. Reviews with status=rejected are excluded.

        Args:
            user_id: The ID of the user to get reviews for.

        Returns:
            A dict with a list of review objects containing id, content, user_id,
            product_id, parent_id, stars, is_anonymous, pic_info, created_at,
            likes, current_user_liked, is_pinned.
        """
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "GET",
            f"{PREFIX}/users/{user_id}/reviews",
        )

    # ─── ADMIN (Merchant) ──────────────────────────────────

    @mcp.tool()
    async def list_reviews_admin(
        ctx: Context,
        product_id: int,
        stars: int = 0,
    ) -> dict[str, Any]:
        """List reviews for moderation. Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).
            product_id: Filter by product ID.
            stars: Filter by star rating (0 = any).

        Returns:
            Reviews list for moderation.
        """
        user = await require_role(ctx, ROLE_MERCHANT_ADMIN)
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
        """Delete a review (moderation). Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to delete.

        Returns:
            Deletion result.
        """
        user = await require_role(ctx, ROLE_MERCHANT_ADMIN)
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
        """Pin or unpin a review. Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to pin/unpin.
            is_pinned: True to pin, False to unpin.

        Returns:
            Pin result.
        """
        user = await require_role(ctx, ROLE_MERCHANT_ADMIN)
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
        """Reply to a review as merchant. Requires merchant_admin role.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to reply to.
            content: Reply text content.

        Returns:
            The created reply.
        """
        user = await require_role(ctx, ROLE_MERCHANT_ADMIN)
        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/merchant/reviews/{review_id}/replies",
            user_id=user.user_id_int,
            json_body={"content": content, "parentID": review_id},
        )

    # ─── AGENT (Internal M2M) ──────────────────────────────

    @mcp.tool()
    async def list_reviews_by_status(
        ctx: Context,
        status: str,
        limit: int = 100,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List reviews filtered by status (internal M2M). No authentication required.

        Valid status values: pending, processing, approved, hidden, rejected.

        Args:
            ctx: MCP context (injected automatically).
            status: Review status to filter by (required).
            limit: Maximum number of items to return (default 100).
            cursor: Pagination cursor from previous response.

        Returns:
            A dict with reviews grouped by status and pagination info.
        """
        if status not in ["pending", "processing", "approved", "hidden", "rejected"]:
            raise ToolError(
                f"Invalid status '{status}'. Must be one of: "
                "pending, processing, approved, hidden, rejected"
            )

        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        client = get_http_client()
        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "GET",
            f"{PREFIX}/reviews/status/{status}",
            params=params,
        )

    @mcp.tool()
    async def update_review_status(
        ctx: Context,
        review_id: str,
        status: str,
        stars: int | None = None,
        is_mismatch: bool | None = None,
        is_harmful: bool | None = None,
        auto_flag: str | None = None,
    ) -> dict[str, Any]:
        """Update review status (internal M2M). No authentication required.

        Valid status values: pending, processing, approved, hidden, rejected.

        Args:
            ctx: MCP context (injected automatically).
            review_id: The review ID to update (required).
            status: New status for the review (required).
            stars: Optional rating score (0-5) to update review rating.
            is_mismatch: Optional flag indicating if review is mismatch.
            is_harmful: Optional flag indicating if review is harmful.
            auto_flag: Optional auto-flag string (e.g., reason for auto-moderation).

        Returns:
            A dict with:
            - err_msg: Error message (empty on success).
            - data: Success message (e.g., "update review success").
        """
        if status not in ["pending", "processing", "approved", "hidden", "rejected"]:
            raise ToolError(
                f"Invalid status '{status}'. Must be one of: "
                "pending, processing, approved, hidden, rejected"
            )

        if not review_id:
            raise ToolError("review_id is required")

        if stars is not None and (stars < 0 or stars > 5):
            raise ToolError("stars must be between 0 and 5")

        client = get_http_client()
        body: dict[str, Any] = {"review_id": review_id, "status": status}

        if stars is not None:
            body["stars"] = stars
        if is_mismatch is not None:
            body["is_mismatch"] = is_mismatch
        if is_harmful is not None:
            body["is_harmful"] = is_harmful
        if auto_flag is not None:
            body["auto_flag"] = auto_flag

        return await client.call(
            get_settings().COMMENT_MS_HTTP,
            "POST",
            f"{PREFIX}/reviews/status",
            json_body=body,
        )
