"""Tests for all MCP tool functions — mocks HTTP client and auth."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from ceramicraft_mcp_server.auth import AuthenticatedUser

MOCK_USER = AuthenticatedUser(user_id="42", roles=["customer"], email="u@test.com")
MOCK_ADMIN = AuthenticatedUser(
    user_id="1", roles=["merchant_admin", "product_editor"], email="a@test.com"
)


def _register(module_path: str, register_func_name: str) -> dict:
    """Import a register function and capture tools via a mock MCP."""
    import importlib

    mod = importlib.import_module(module_path)
    register_fn = getattr(mod, register_func_name)

    tools: dict = {}

    def capture_tool():
        def decorator(func):
            tools[func.__name__] = func
            return func

        return decorator

    mcp = MagicMock()
    mcp.tool = capture_tool
    register_fn(mcp)
    return tools


def _mock_http(return_value=None):
    """Create a mocked HTTP client."""
    mock_client = MagicMock()
    mock_client.call = AsyncMock(return_value=return_value or {"success": True})
    return mock_client


def _user_ctx():
    ctx = MagicMock()
    ctx.request_context.request.headers = {"authorization": "Bearer user-token"}
    return ctx


def _admin_ctx():
    ctx = MagicMock()
    ctx.request_context.request.headers = {"authorization": "Bearer admin-token"}
    ctx.meta = None
    return ctx


def _patch_user(module_name: str, http_mock):
    """Context manager to patch auth + http for USER tools."""
    return (
        patch(
            "ceramicraft_mcp_server.auth.verify_token",
            AsyncMock(return_value=MOCK_USER),
        ),
        patch(
            f"ceramicraft_mcp_server.tools.{module_name}.get_http_client",
            return_value=http_mock,
        ),
    )


def _patch_admin(module_name: str, http_mock):
    """Context manager to patch auth + http for ADMIN tools."""
    return (
        patch(
            "ceramicraft_mcp_server.auth.verify_token",
            AsyncMock(return_value=MOCK_ADMIN),
        ),
        patch(
            f"ceramicraft_mcp_server.tools.{module_name}.get_http_client",
            return_value=http_mock,
        ),
    )


# ─── Product tools ─────────────────────────────────────────


PRODUCT_TOOLS = _register(
    "ceramicraft_mcp_server.tools.product", "register_product_tools"
)


@pytest.mark.asyncio
async def test_search_products():
    http = _mock_http({"products": [{"id": 1, "price": 3500}]})
    with patch(
        "ceramicraft_mcp_server.tools.product.get_http_client", return_value=http
    ):
        result = await PRODUCT_TOOLS["search_products"]("vase", "", 0, 0)
        assert "products" in result
        assert result["products"][0]["price"] == 35.0
        assert result["products"][0]["price_cents"] == 3500
        assert result["products"][0]["price_display"] == "S$35.00"
        http.call.assert_called_once()
        assert http.call.call_args.args[1] == "GET"


@pytest.mark.asyncio
async def test_get_product():
    http = _mock_http({"id": 1, "name": "Bowl", "price": 2800})
    with patch(
        "ceramicraft_mcp_server.tools.product.get_http_client", return_value=http
    ):
        result = await PRODUCT_TOOLS["get_product"](1)
        assert result["id"] == 1
        assert result["price"] == 28.0
        assert result["price_cents"] == 2800


@pytest.mark.asyncio
async def test_create_product():
    http = _mock_http({"id": 1})
    p1, p2 = _patch_admin("product", http)
    with p1, p2:
        await PRODUCT_TOOLS["create_product"](
            _admin_ctx(), "Vase", "A vase", 1000, "vase", 10
        )
        body = http.call.call_args.kwargs["json_body"]
        assert body["name"] == "Vase"
        assert body["desc"] == "A vase"
        assert body["price"] == 1000


@pytest.mark.asyncio
async def test_create_product_requires_admin():
    http = _mock_http()
    with (
        patch(
            "ceramicraft_mcp_server.auth.verify_token",
            AsyncMock(return_value=MOCK_USER),
        ),
        patch(
            "ceramicraft_mcp_server.tools.product.get_http_client", return_value=http
        ),
    ):
        with pytest.raises(ToolError, match="Access denied"):
            await PRODUCT_TOOLS["create_product"](
                _user_ctx(), "Vase", "A vase", 1000, "vase", 10
            )


@pytest.mark.asyncio
async def test_update_product():
    http = _mock_http({"id": 1})
    p1, p2 = _patch_admin("product", http)
    with p1, p2:
        await PRODUCT_TOOLS["update_product"](_admin_ctx(), 1, name="New Name")
        body = http.call.call_args.kwargs["json_body"]
        assert body["name"] == "New Name"
        assert body["id"] == 1


@pytest.mark.asyncio
async def test_update_product_status():
    http = _mock_http()
    p1, p2 = _patch_admin("product", http)
    with p1, p2:
        await PRODUCT_TOOLS["update_product_status"](_admin_ctx(), 1, 1)
        body = http.call.call_args.kwargs["json_body"]
        assert body["status"] == 1


@pytest.mark.asyncio
async def test_update_product_stock():
    http = _mock_http()
    p1, p2 = _patch_admin("product", http)
    with p1, p2:
        await PRODUCT_TOOLS["update_product_stock"](_admin_ctx(), 1, 50)
        body = http.call.call_args.kwargs["json_body"]
        assert body["stock"] == 50


@pytest.mark.asyncio
async def test_get_merchant_product():
    http = _mock_http({"id": 1})
    p1, p2 = _patch_admin("product", http)
    with p1, p2:
        await PRODUCT_TOOLS["get_merchant_product"](_admin_ctx(), 1)
        assert http.call.call_args.kwargs["user_id"] == 1


@pytest.mark.asyncio
async def test_list_merchant_products():
    http = _mock_http({"products": []})
    p1, p2 = _patch_admin("product", http)
    with p1, p2:
        await PRODUCT_TOOLS["list_merchant_products"](_admin_ctx(), "vase")
        assert http.call.call_args.kwargs.get("params", {}).get("keyword") == "vase"


@pytest.mark.asyncio
async def test_get_image_upload_url():
    http = _mock_http({"url": "https://s3.example.com/upload"})
    p1, p2 = _patch_admin("product", http)
    with p1, p2:
        await PRODUCT_TOOLS["get_image_upload_url"](_admin_ctx(), "png")
        body = http.call.call_args.kwargs["json_body"]
        assert body["image_type"] == "png"


# ─── Cart tools ────────────────────────────────────────────


CART_TOOLS = _register("ceramicraft_mcp_server.tools.cart", "register_cart_tools")


@pytest.mark.asyncio
async def test_get_cart():
    http = _mock_http(
        {
            "cart_items": [
                {"product_info": {"id": 1, "price": 3500}, "total_price": 7000}
            ],
            "selected_price": 7000,
        }
    )
    p1, p2 = _patch_user("cart", http)
    with p1, p2:
        result = await CART_TOOLS["get_cart"](_user_ctx())
        assert result["cart_items"][0]["product_info"]["price"] == 35.0
        assert result["cart_items"][0]["total_price"] == 70.0
        assert result["selected_price"] == 70.0
        assert http.call.call_args.kwargs["user_id"] == 42


@pytest.mark.asyncio
async def test_add_to_cart():
    http = _mock_http({"id": 1})
    p1, p2 = _patch_user("cart", http)
    with p1, p2:
        await CART_TOOLS["add_to_cart"](_user_ctx(), 5, 2, True)
        body = http.call.call_args.kwargs["json_body"]
        assert body["product_id"] == 5
        assert body["quantity"] == 2
        assert body["selected"] is True


@pytest.mark.asyncio
async def test_update_cart_item():
    http = _mock_http()
    p1, p2 = _patch_user("cart", http)
    with p1, p2:
        await CART_TOOLS["update_cart_item"](_user_ctx(), 1, product_id=10, quantity=3)
        body = http.call.call_args.kwargs["json_body"]
        assert body["product_id"] == 10
        assert body["quantity"] == 3
        assert body["selected"] is True


@pytest.mark.asyncio
async def test_remove_cart_item():
    http = _mock_http()
    p1, p2 = _patch_user("cart", http)
    with p1, p2:
        await CART_TOOLS["remove_cart_item"](_user_ctx(), 1)
        assert http.call.call_args.args[1] == "DELETE"


@pytest.mark.asyncio
async def test_estimate_cart_price():
    http = _mock_http(
        {"product_price": 3500, "shipping_price": 500, "tax": 100, "total": 4100}
    )
    p1, p2 = _patch_user("cart", http)
    with p1, p2:
        result = await CART_TOOLS["estimate_cart_price"](_user_ctx())
        assert result["product_price"] == 35.0
        assert result["shipping_price"] == 5.0
        assert result["tax"] == 1.0
        assert result["total"] == 41.0
        assert result["total_cents"] == 4100
        assert result["total_display"] == "S$41.00"


# ─── Order tools ───────────────────────────────────────────


ORDER_TOOLS = _register("ceramicraft_mcp_server.tools.order", "register_order_tools")


@pytest.mark.asyncio
async def test_create_order():
    http = _mock_http({"order_no": "ORD-001", "pay_amount": 4100})
    p1, p2 = _patch_user("order", http)
    with p1, p2:
        result = await ORDER_TOOLS["create_order"](
            _user_ctx(), "John", "Doe", "+65123", "123 Street", "SG", 123456
        )
        assert result["pay_amount"] == 41.0
        assert result["pay_amount_cents"] == 4100
        body = http.call.call_args.kwargs["json_body"]
        assert body["receiver_first_name"] == "John"
        assert body["receiver_country"] == "SG"
        assert body["receiver_zip_code"] == 123456


@pytest.mark.asyncio
async def test_list_my_orders():
    http = _mock_http(
        {"orders": [{"order_no": "ORD-001", "total_amount": 4100}], "total": 1}
    )
    p1, p2 = _patch_user("order", http)
    with p1, p2:
        result = await ORDER_TOOLS["list_my_orders"](_user_ctx(), 10, 0, "2026-01-01")
        assert result["orders"][0]["total_amount"] == 41.0
        assert result["orders"][0]["total_amount_cents"] == 4100
        body = http.call.call_args.kwargs["json_body"]
        assert body["limit"] == 10
        assert body["start_time"] == "2026-01-01"


@pytest.mark.asyncio
async def test_get_order_detail():
    http = _mock_http(
        {
            "order_no": "ORD-001",
            "total_amount": 4100,
            "items": [{"price": 3500, "total_price": 7000}],
        }
    )
    p1, p2 = _patch_user("order", http)
    with p1, p2:
        result = await ORDER_TOOLS["get_order_detail"](_user_ctx(), "ORD-001")
        assert "ORD-001" in http.call.call_args.args[2]
        assert result["total_amount"] == 41.0
        assert result["items"][0]["price"] == 35.0
        assert result["items"][0]["total_price"] == 70.0


@pytest.mark.asyncio
async def test_confirm_receipt():
    http = _mock_http()
    p1, p2 = _patch_user("order", http)
    with p1, p2:
        await ORDER_TOOLS["confirm_receipt"](_user_ctx(), "ORD-001")
        body = http.call.call_args.kwargs["json_body"]
        assert body["order_no"] == "ORD-001"


@pytest.mark.asyncio
async def test_get_order_stats():
    http = _mock_http({"total_orders": 100})
    p1, p2 = _patch_admin("order", http)
    with p1, p2:
        result = await ORDER_TOOLS["get_order_stats"](_admin_ctx())
        assert result["total_orders"] == 100


@pytest.mark.asyncio
async def test_list_merchant_orders():
    http = _mock_http({"orders": []})
    p1, p2 = _patch_admin("order", http)
    with p1, p2:
        await ORDER_TOOLS["list_merchant_orders"](_admin_ctx(), order_no="ORD-001")
        body = http.call.call_args.kwargs["json_body"]
        assert body["order_no"] == "ORD-001"


@pytest.mark.asyncio
async def test_get_merchant_order_detail():
    http = _mock_http({"order_no": "ORD-001"})
    p1, p2 = _patch_admin("order", http)
    with p1, p2:
        await ORDER_TOOLS["get_merchant_order_detail"](_admin_ctx(), "ORD-001")


@pytest.mark.asyncio
async def test_ship_order():
    http = _mock_http()
    p1, p2 = _patch_admin("order", http)
    with p1, p2:
        await ORDER_TOOLS["ship_order"](_admin_ctx(), "ORD-001", "TRACK-123")
        body = http.call.call_args.kwargs["json_body"]
        assert body["tracking_no"] == "TRACK-123"


# ─── Comment tools ─────────────────────────────────────────


COMMENT_TOOLS = _register(
    "ceramicraft_mcp_server.tools.comment", "register_comment_tools"
)


@pytest.mark.asyncio
async def test_list_product_reviews():
    http = _mock_http({"reviews": []})
    p1, p2 = _patch_user("comment", http)
    with p1, p2:
        result = await COMMENT_TOOLS["list_product_reviews"](_user_ctx(), 1)
        assert "reviews" in result


@pytest.mark.asyncio
async def test_get_user_reviews():
    http = _mock_http({"reviews": []})
    p1, p2 = _patch_user("comment", http)
    with p1, p2:
        await COMMENT_TOOLS["get_user_reviews"](_user_ctx())


@pytest.mark.asyncio
async def test_create_review_invalid_stars():
    with pytest.raises(ToolError, match="Stars must be between 1 and 5"):
        await COMMENT_TOOLS["create_review"](_user_ctx(), 1, "Great!", 6)


@pytest.mark.asyncio
async def test_create_review():
    http = _mock_http({"review_id": "r1"})
    p1, p2 = _patch_user("comment", http)
    with p1, p2:
        await COMMENT_TOOLS["create_review"](
            _user_ctx(), 1, "Great!", 5, False, ["img.jpg"]
        )
        body = http.call.call_args.kwargs["json_body"]
        assert body["productID"] == 1
        assert body["stars"] == 5
        assert body["pic_info"] == ["img.jpg"]


@pytest.mark.asyncio
async def test_like_review():
    http = _mock_http()
    p1, p2 = _patch_user("comment", http)
    with p1, p2:
        await COMMENT_TOOLS["like_review"](_user_ctx(), "r1")
        body = http.call.call_args.kwargs["json_body"]
        assert body["review_id"] == "r1"


@pytest.mark.asyncio
async def test_list_reviews_by_user_id():
    http = _mock_http(
        {
            "status": 0,
            "msg": "ok",
            "data": [
                {
                    "id": "r1",
                    "content": "Great product!",
                    "user_id": 42,
                    "product_id": 1,
                    "parent_id": None,
                    "stars": 5,
                    "is_anonymous": False,
                    "pic_info": [],
                    "created_at": "2026-01-01T00:00:00Z",
                    "likes": 10,
                    "current_user_liked": False,
                    "is_pinned": False,
                }
            ],
        }
    )
    with patch(
        "ceramicraft_mcp_server.tools.comment.get_http_client", return_value=http
    ):
        result = await COMMENT_TOOLS["list_reviews_by_user_id"](42)
        assert result["status"] == 0
        assert len(result["data"]) == 1
        assert result["data"][0]["user_id"] == 42
        assert http.call.call_args.args[1] == "GET"
        assert "/users/42/reviews" in http.call.call_args.args[2]


@pytest.mark.asyncio
async def test_list_reviews_admin():
    http = _mock_http({"reviews": []})
    p1, p2 = _patch_admin("comment", http)
    with p1, p2:
        await COMMENT_TOOLS["list_reviews_admin"](_admin_ctx(), 1, 5)
        body = http.call.call_args.kwargs["json_body"]
        assert body["product_id"] == 1
        assert body["stars"] == 5


@pytest.mark.asyncio
async def test_delete_review():
    http = _mock_http()
    p1, p2 = _patch_admin("comment", http)
    with p1, p2:
        await COMMENT_TOOLS["delete_review"](_admin_ctx(), "r1")
        assert http.call.call_args.args[1] == "DELETE"


@pytest.mark.asyncio
async def test_pin_review():
    http = _mock_http()
    p1, p2 = _patch_admin("comment", http)
    with p1, p2:
        await COMMENT_TOOLS["pin_review"](_admin_ctx(), "r1", True)
        body = http.call.call_args.kwargs["json_body"]
        assert body["is_pinned"] is True


@pytest.mark.asyncio
async def test_reply_to_review():
    http = _mock_http()
    p1, p2 = _patch_admin("comment", http)
    with p1, p2:
        await COMMENT_TOOLS["reply_to_review"](_admin_ctx(), "r1", "Thanks!")
        body = http.call.call_args.kwargs["json_body"]
        assert body["content"] == "Thanks!"
        assert body["parentID"] == "r1"


# ─── Public tools (moderation, no auth) ────────────────────────────


@pytest.mark.asyncio
async def test_list_reviews_by_status():
    http = _mock_http(
        {
            "err_msg": "",
            "data": {
                "items": [
                    {
                        "id": "r1",
                        "content": "Great product!",
                        "user_id": "u1",
                        "product_id": 1,
                        "parent_id": None,
                        "stars": 5,
                        "is_anonymous": False,
                        "is_pinned": False,
                        "pic_info": [],
                        "status": "pending",
                        "is_mismatch": False,
                        "is_harmful": False,
                        "auto_flag": None,
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ],
                "next_cursor": None,
            },
        }
    )
    with patch(
        "ceramicraft_mcp_server.tools.comment.get_http_client", return_value=http
    ):
        result = await COMMENT_TOOLS["list_reviews_by_status"](_user_ctx(), "pending")
        assert result["data"]["items"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_list_reviews_by_status_invalid_status():
    with pytest.raises(ToolError, match="Invalid status"):
        await COMMENT_TOOLS["list_reviews_by_status"](_user_ctx(), "invalid_status")


@pytest.mark.asyncio
async def test_update_review_status():
    http = _mock_http({"err_msg": "", "data": "update review success"})
    with patch(
        "ceramicraft_mcp_server.tools.comment.get_http_client", return_value=http
    ):
        result = await COMMENT_TOOLS["update_review_status"](
            _user_ctx(), "r1", "processing"
        )
        assert result["data"] == "update review success"
        body = http.call.call_args.kwargs["json_body"]
        assert body["review_id"] == "r1"
        assert body["status"] == "processing"


@pytest.mark.asyncio
async def test_update_review_status_with_all_fields():
    http = _mock_http({"err_msg": "", "data": "update review success"})
    with patch(
        "ceramicraft_mcp_server.tools.comment.get_http_client", return_value=http
    ):
        await COMMENT_TOOLS["update_review_status"](
            _user_ctx(),
            "r1",
            "rejected",
            stars=3,
            is_mismatch=True,
            is_harmful=True,
            auto_flag="spam",
        )
        body = http.call.call_args.kwargs["json_body"]
        assert body["review_id"] == "r1"
        assert body["status"] == "rejected"
        assert body["stars"] == 3
        assert body["is_mismatch"] is True
        assert body["is_harmful"] is True
        assert body["auto_flag"] == "spam"


@pytest.mark.asyncio
async def test_update_review_status_invalid_status():
    with pytest.raises(ToolError, match="Invalid status"):
        await COMMENT_TOOLS["update_review_status"](_user_ctx(), "r1", "invalid_status")


@pytest.mark.asyncio
async def test_update_review_status_invalid_stars():
    with pytest.raises(ToolError, match="stars must be between 0 and 5"):
        await COMMENT_TOOLS["update_review_status"](
            _user_ctx(), "r1", "approved", stars=6
        )


@pytest.mark.asyncio
async def test_update_review_status_missing_review_id():
    with pytest.raises(ToolError, match="review_id is required"):
        await COMMENT_TOOLS["update_review_status"](_user_ctx(), "", "pending")


USER_TOOLS = _register("ceramicraft_mcp_server.tools.user", "register_user_tools")


@pytest.mark.asyncio
async def test_get_my_profile():
    http = _mock_http({"name": "Test User"})
    p1, p2 = _patch_user("user", http)
    with p1, p2:
        result = await USER_TOOLS["get_my_profile"](_user_ctx())
        assert result["name"] == "Test User"


@pytest.mark.asyncio
async def test_update_my_profile():
    http = _mock_http()
    p1, p2 = _patch_user("user", http)
    with p1, p2:
        await USER_TOOLS["update_my_profile"](
            _user_ctx(), name="New Name", email="new@test.com"
        )
        body = http.call.call_args.kwargs["json_body"]
        assert body["id"] == 42
        assert body["name"] == "New Name"
        assert body["email"] == "new@test.com"


@pytest.mark.asyncio
async def test_list_my_addresses():
    http = _mock_http({"addresses": []})
    p1, p2 = _patch_user("user", http)
    with p1, p2:
        await USER_TOOLS["list_my_addresses"](_user_ctx())


@pytest.mark.asyncio
async def test_create_address():
    http = _mock_http({"id": 1})
    p1, p2 = _patch_user("user", http)
    with p1, p2:
        await USER_TOOLS["create_address"](
            _user_ctx(),
            first_name="John",
            last_name="Doe",
            contact_phone="+65123",
            detail="123 Street",
            country="SG",
            zip_code="123456",
            city="Singapore",
        )
        body = http.call.call_args.kwargs["json_body"]
        assert body["first_name"] == "John"
        assert body["last_name"] == "Doe"
        assert body["contact_phone"] == "+65123"
        assert body["detail"] == "123 Street"
        assert body["country"] == "SG"
        assert body["zip_code"] == "123456"
        assert body["city"] == "Singapore"


@pytest.mark.asyncio
async def test_update_address():
    http = _mock_http()
    p1, p2 = _patch_user("user", http)
    with p1, p2:
        await USER_TOOLS["update_address"](
            _user_ctx(), 1, first_name="Jane", city="NYC"
        )
        body = http.call.call_args.kwargs["json_body"]
        assert body["first_name"] == "Jane"
        assert body["city"] == "NYC"


@pytest.mark.asyncio
async def test_delete_address():
    http = _mock_http()
    p1, p2 = _patch_user("user", http)
    with p1, p2:
        await USER_TOOLS["delete_address"](_user_ctx(), 1)
        assert http.call.call_args.args[1] == "DELETE"
        assert "/addresses/1" in http.call.call_args.args[2]


# ─── Payment tools ─────────────────────────────────────────


PAYMENT_TOOLS = _register(
    "ceramicraft_mcp_server.tools.payment", "register_payment_tools"
)


@pytest.mark.asyncio
async def test_get_pay_account():
    http = _mock_http({"balance": 1000})
    p1, p2 = _patch_user("payment", http)
    with p1, p2:
        result = await PAYMENT_TOOLS["get_pay_account"](_user_ctx())
        assert result["balance"] == 10.0
        assert result["balance_cents"] == 1000


@pytest.mark.asyncio
async def test_top_up_account():
    http = _mock_http({"current_balance": 5000, "top_up_amount": 1000})
    p1, p2 = _patch_user("payment", http)
    with p1, p2:
        result = await PAYMENT_TOOLS["top_up_account"](_user_ctx(), "CODE-123")
        assert result["current_balance"] == 50.0
        assert result["top_up_amount"] == 10.0
        body = http.call.call_args.kwargs["json_body"]
        assert body == {"redeem_code": "CODE-123"}


@pytest.mark.asyncio
async def test_list_redeem_codes():
    http = _mock_http({"codes": []})
    p1, p2 = _patch_admin("payment", http)
    with p1, p2:
        await PAYMENT_TOOLS["list_redeem_codes"](_admin_ctx(), "ABC", 10, False)
        params = http.call.call_args.kwargs["params"]
        assert params["code"] == "ABC"
        assert params["limit"] == 10
        assert params["used"] is False


@pytest.mark.asyncio
async def test_generate_redeem_codes():
    http = _mock_http({"codes": ["A", "B"]})
    p1, p2 = _patch_admin("payment", http)
    with p1, p2:
        await PAYMENT_TOOLS["generate_redeem_codes"](_admin_ctx(), 100, 5)
        params = http.call.call_args.kwargs["params"]
        assert params == {"amount": 100, "count": 5}


# ─── Notification tools ────────────────────────────────────


NOTIFICATION_TOOLS = _register(
    "ceramicraft_mcp_server.tools.notification", "register_notification_tools"
)


@pytest.mark.asyncio
async def test_register_push_token():
    http = _mock_http({"aes_key": "abc123"})
    p1, p2 = _patch_user("notification", http)
    with p1, p2:
        await NOTIFICATION_TOOLS["register_push_token"](
            _user_ctx(), "device-1", "fcm-abc"
        )
        call_kwargs = http.call.call_args.kwargs
        assert call_kwargs["user_id"] == 42
        body = call_kwargs["json_body"]
        assert body["device_id"] == "device-1"
        assert body["fcm_token"] == "fcm-abc"
        assert "user_id" not in body
