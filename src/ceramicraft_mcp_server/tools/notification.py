"""Notification-related MCP tools.

USER tools: register_push_token
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_user
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
            user_id=user.user_id_int,
            json_body={
                "device_id": device_id,
                "fcm_token": fcm_token,
            },
        )
