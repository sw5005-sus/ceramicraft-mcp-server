"""Notification-related MCP tools.

USER tools: register_push_token
ADMIN tools: send_push_notification (via gRPC)
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_admin, require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client

PREFIX = "/notification-ms/v1"


def register_notification_tools(mcp: FastMCP) -> None:
    """Register notification tools on the MCP server."""

    @mcp.tool()
    async def register_push_token(
        ctx: Context,
        device_id: str,
        fcm_token: str,
    ) -> dict[str, Any]:
        """Register a device push notification token. Requires authentication.

        Args:
            ctx: MCP context (injected automatically).
            device_id: Unique device identifier.
            fcm_token: Firebase Cloud Messaging token for the device.

        Returns:
            Registration result including AES key.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().NOTIFICATION_MS_HTTP,
            "POST",
            f"{PREFIX}/push-token",
            json_body={
                "user_id": user.user_id_int,
                "device_id": device_id,
                "fcm_token": fcm_token,
            },
        )

    @mcp.tool()
    async def send_push_notification(
        ctx: Context,
        target_user_id: int,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a push notification to a user. Requires admin role.

        This will use gRPC to call notification-ms SendUserPush.
        Currently returns a placeholder until gRPC client is implemented.

        Args:
            ctx: MCP context (injected automatically).
            target_user_id: Target user ID to send notification to.
            title: Notification title.
            body: Notification body text.
            data: Optional key-value data payload.

        Returns:
            Send result including success status and sent count.
        """
        await require_admin(ctx)
        # TODO: Replace with gRPC call to notification-ms SendUserPush
        return {
            "success": False,
            "message": "gRPC client not yet implemented. Use direct gRPC call.",
            "target_user_id": target_user_id,
            "title": title,
            "body": body,
            "data": data or {},
        }
