"""Tests for MCP server application."""

from ceramicraft_mcp_server.app import create_mcp_server


def test_create_mcp_server():
    """create_mcp_server() should return a FastMCP instance."""
    mcp = create_mcp_server()
    assert mcp is not None
    assert mcp.name == "CeramiCraft MCP Server"


def test_mcp_server_has_tools():
    """All expected tools should be registered."""
    mcp = create_mcp_server()
    tools = mcp._tool_manager.list_tools()
    tool_names = {t.name for t in tools}

    # PUBLIC product tools
    assert "search_products" in tool_names
    assert "get_product" in tool_names

    # ADMIN product tools
    assert "create_product" in tool_names
    assert "update_product" in tool_names
    assert "update_product_status" in tool_names
    assert "update_product_stock" in tool_names
    assert "get_merchant_product" in tool_names
    assert "list_merchant_products" in tool_names
    assert "get_image_upload_url" in tool_names

    # Cart tools (USER)
    assert "get_cart" in tool_names
    assert "add_to_cart" in tool_names
    assert "update_cart_item" in tool_names
    assert "remove_cart_item" in tool_names
    assert "estimate_cart_price" in tool_names

    # Comment tools
    assert "list_product_reviews" in tool_names
    assert "get_user_reviews" in tool_names
    assert "create_review" in tool_names
    assert "like_review" in tool_names
    assert "list_reviews_by_user_id" in tool_names
    assert "list_reviews_admin" in tool_names
    assert "delete_review" in tool_names
    assert "pin_review" in tool_names
    assert "reply_to_review" in tool_names
    assert "list_reviews_by_status" in tool_names
    assert "update_review_status" in tool_names

    # Order tools
    assert "create_order" in tool_names
    assert "list_my_orders" in tool_names
    assert "get_order_detail" in tool_names
    assert "confirm_receipt" in tool_names
    assert "get_order_stats" in tool_names
    assert "list_merchant_orders" in tool_names
    assert "get_merchant_order_detail" in tool_names
    assert "ship_order" in tool_names

    # User tools
    assert "get_my_profile" in tool_names
    assert "update_my_profile" in tool_names
    assert "list_my_addresses" in tool_names
    assert "create_address" in tool_names
    assert "update_address" in tool_names
    assert "delete_address" in tool_names

    # Payment tools
    assert "get_pay_account" in tool_names
    assert "top_up_account" in tool_names
    assert "list_redeem_codes" in tool_names
    assert "generate_redeem_codes" in tool_names

    # Notification tools
    assert "register_push_token" in tool_names


def test_mcp_server_tool_count():
    """Should have exactly 44 tools registered."""
    mcp = create_mcp_server()
    tools = mcp._tool_manager.list_tools()
    assert len(tools) == 44
