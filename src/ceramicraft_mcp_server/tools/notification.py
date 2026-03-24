"""Notification-related MCP tools (require authentication)."""

from mcp.server.fastmcp import Context, FastMCP


def register_notification_tools(mcp: FastMCP) -> None:
    """Register notification tools on the MCP server."""

    @mcp.tool()
    async def register_push_token(
        ctx: Context, token: str, device_type: str = "android"
    ) -> dict:
        """Register a device push notification token.

        Args:
            ctx: MCP context (injected automatically).
            token: FCM device token.
            device_type: Device type (android/ios).

        Returns:
            Registration result.
        """
        # TODO: Extract user_id from ctx, call notification-ms gRPC/HTTP
        _ = ctx
        return {"success": True, "device_type": device_type}
