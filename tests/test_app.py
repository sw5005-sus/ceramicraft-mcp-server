"""Tests for MCP server app creation and tool registration."""

from ceramicraft_mcp_server.app import create_mcp_server


def test_create_mcp_server():
    """MCP server should be created successfully."""
    mcp = create_mcp_server()
    assert mcp is not None
    assert mcp.name == "CeramiCraft MCP Server"


async def test_mcp_server_has_tools():
    """MCP server should have registered tools."""
    mcp = create_mcp_server()
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]

    # Public tools
    assert "search_products" in tool_names
    assert "get_product" in tool_names
    assert "list_product_categories" in tool_names

    # Comment tools
    assert "list_comments" in tool_names
    assert "add_comment" in tool_names

    # Auth-required tools
    assert "list_my_orders" in tool_names
    assert "get_order_detail" in tool_names
    assert "get_my_profile" in tool_names
    assert "list_my_addresses" in tool_names

    # Admin tools
    assert "query_audit_logs" in tool_names
    assert "verify_audit_chain" in tool_names
