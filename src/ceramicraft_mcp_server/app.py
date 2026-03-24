"""MCP Server application factory."""

from mcp.server.fastmcp import FastMCP

from ceramicraft_mcp_server.tools.comment import register_comment_tools
from ceramicraft_mcp_server.tools.log import register_log_tools
from ceramicraft_mcp_server.tools.notification import register_notification_tools
from ceramicraft_mcp_server.tools.order import register_order_tools
from ceramicraft_mcp_server.tools.product import register_product_tools
from ceramicraft_mcp_server.tools.user import register_user_tools


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all tools registered."""
    mcp = FastMCP(
        "CeramiCraft MCP Server",
        json_response=True,
    )

    # Register tool groups
    register_product_tools(mcp)  # Public tools
    register_comment_tools(mcp)  # Mixed (read=public, write=auth)
    register_order_tools(mcp)  # Auth required
    register_user_tools(mcp)  # Auth required
    register_notification_tools(mcp)  # Auth required
    register_log_tools(mcp)  # Admin only

    return mcp
