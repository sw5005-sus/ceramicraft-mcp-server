"""MCP Server application factory."""

from mcp.server.fastmcp import FastMCP

from ceramicraft_mcp_server.tools.cart import register_cart_tools
from ceramicraft_mcp_server.tools.comment import register_comment_tools
from ceramicraft_mcp_server.tools.log import register_log_tools
from ceramicraft_mcp_server.tools.notification import register_notification_tools
from ceramicraft_mcp_server.tools.order import register_order_tools
from ceramicraft_mcp_server.tools.payment import register_payment_tools
from ceramicraft_mcp_server.tools.product import register_product_tools
from ceramicraft_mcp_server.tools.user import register_user_tools


def create_mcp_server(host: str = "0.0.0.0", port: int = 8080) -> FastMCP:
    """Create and configure the MCP server with all tools registered."""
    mcp = FastMCP(
        "CeramiCraft MCP Server",
        json_response=True,
        host=host,
        port=port,
    )

    # Register tool groups
    register_product_tools(mcp)  # PUBLIC + ADMIN
    register_cart_tools(mcp)  # USER
    register_comment_tools(mcp)  # PUBLIC + USER + ADMIN
    register_order_tools(mcp)  # USER + ADMIN
    register_user_tools(mcp)  # USER
    register_payment_tools(mcp)  # USER + ADMIN
    register_notification_tools(mcp)  # USER + ADMIN
    register_log_tools(mcp)  # ADMIN

    return mcp
