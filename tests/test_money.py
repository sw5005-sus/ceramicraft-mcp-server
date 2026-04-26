from ceramicraft_mcp_server.tools.money import with_display_money_fields


def test_with_display_money_fields_recursively_formats_money_keys():
    result = with_display_money_fields(
        {
            "price": 3500,
            "nested": [{"total_price": 7000, "selected": True}],
            "count": 3500,
        },
        {"price", "total_price"},
    )

    assert result["price"] == 35.0
    assert result["price_cents"] == 3500
    assert result["price_display"] == "$35.00"
    assert result["nested"][0]["total_price"] == 70.0
    assert result["nested"][0]["total_price_cents"] == 7000
    assert result["nested"][0]["selected"] is True
    assert result["count"] == 3500


def test_with_display_money_fields_preserves_existing_trace_fields():
    result = with_display_money_fields(
        {"price": 3500, "price_cents": 1234, "price_display": "$12.34"},
        {"price"},
    )

    assert result["price"] == 35.0
    assert result["price_cents"] == 1234
    assert result["price_display"] == "$12.34"
