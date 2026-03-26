# ceramicraft-mcp-server

MCP Server for the CeramiCraft multi-agent e-commerce platform. Bridges AI agents and backend microservices via [Model Context Protocol](https://modelcontextprotocol.io).

```
AI Agents ──MCP (Streamable HTTP)──▶ MCP Server ──HTTP──▶ Backend Microservices
```

## Tool Catalog (41 tools)

### Product (9 tools)

| Tool | Auth | Backend | Description |
|------|------|---------|-------------|
| `search_products` | PUBLIC | product-ms | Search products by keyword, category, price range |
| `get_product` | PUBLIC | product-ms | Get product detail by ID |
| `create_product` | ADMIN (`merchant_admin`, `product_editor`) | product-ms | Create a new product listing |
| `update_product` | ADMIN (`merchant_admin`, `product_editor`) | product-ms | Edit product info (name, desc, price, ceramic attributes) |
| `update_product_status` | ADMIN (`merchant_admin`, `product_auditor`) | product-ms | Publish / unpublish a product |
| `update_product_stock` | ADMIN (`merchant_admin`, `product_editor`) | product-ms | Update inventory stock |
| `get_merchant_product` | ADMIN (all) | product-ms | Get full merchant-view product detail |
| `list_merchant_products` | ADMIN (all) | product-ms | List products (merchant dashboard) |
| `get_image_upload_url` | ADMIN (`merchant_admin`, `product_editor`) | product-ms | Get presigned URL for image upload |

### Cart (5 tools)

| Tool | Auth | Backend | Description |
|------|------|---------|-------------|
| `get_cart` | USER | product-ms | View user's cart |
| `add_to_cart` | USER | product-ms | Add item to cart |
| `update_cart_item` | USER | product-ms | Update cart item quantity / selection |
| `remove_cart_item` | USER | product-ms | Remove item from cart |
| `estimate_cart_price` | USER | product-ms | Calculate cart total before checkout |

### Order (8 tools)

| Tool | Auth | Backend | Description |
|------|------|---------|-------------|
| `create_order` | USER | order-ms | Place an order with receiver info |
| `list_my_orders` | USER | order-ms | List user's order history |
| `get_order_detail` | USER | order-ms | Get order detail by order number |
| `confirm_receipt` | USER | order-ms | Confirm delivery received |
| `get_order_stats` | ADMIN (`merchant_admin`) | order-ms | Get order statistics dashboard |
| `list_merchant_orders` | ADMIN (`merchant_admin`) | order-ms | List orders (merchant view, filterable) |
| `get_merchant_order_detail` | ADMIN (`merchant_admin`) | order-ms | Get order detail (merchant view) |
| `ship_order` | ADMIN (`merchant_admin`) | order-ms | Ship an order with tracking number |

### Review (8 tools)

| Tool | Auth | Backend | Description |
|------|------|---------|-------------|
| `list_product_reviews` | PUBLIC | comment-ms | Get reviews for a product |
| `get_user_reviews` | USER | comment-ms | Get current user's reviews |
| `create_review` | USER | comment-ms | Post a product review |
| `like_review` | USER | comment-ms | Like a review |
| `list_reviews_admin` | ADMIN (`merchant_admin`) | comment-ms | List reviews with filters (moderation) |
| `delete_review` | ADMIN (`merchant_admin`) | comment-ms | Delete a review |
| `pin_review` | ADMIN (`merchant_admin`) | comment-ms | Pin / unpin a review |
| `reply_to_review` | ADMIN (`merchant_admin`) | comment-ms | Reply to a review as merchant |

### User (6 tools)

| Tool | Auth | Backend | Description |
|------|------|---------|-------------|
| `get_my_profile` | USER | user-ms | Get user profile |
| `update_my_profile` | USER | user-ms | Update name / email / avatar |
| `list_my_addresses` | USER | user-ms | List shipping addresses |
| `create_address` | USER | user-ms | Add a shipping address |
| `update_address` | USER | user-ms | Edit a shipping address |
| `delete_address` | USER | user-ms | Delete a shipping address |

### Payment (4 tools)

| Tool | Auth | Backend | Description |
|------|------|---------|-------------|
| `get_pay_account` | USER | payment-ms | Get wallet balance |
| `top_up_account` | USER | payment-ms | Top up with redeem code |
| `list_redeem_codes` | ADMIN (`merchant_admin`) | payment-ms | Query redeem codes |
| `generate_redeem_codes` | ADMIN (`merchant_admin`) | payment-ms | Generate new redeem codes |

### Notification (1 tool)

| Tool | Auth | Backend | Description |
|------|------|---------|-------------|
| `register_push_token` | USER | notification-ms | Register FCM device push token |

### Summary

| Auth Level | Count | Description |
|------------|-------|-------------|
| PUBLIC | 3 | No authentication needed |
| USER | 21 | Requires valid Zitadel JWT |
| ADMIN | 17 | Per-tool role check (see table above for specific roles) |

## Auth

JWT tokens are verified against [Zitadel](https://zitadel.com) JWKS. User identity is extracted from the `sub` claim and passed to backends via `X-Original-User-ID` header.

## Development

```bash
# Install
uv sync

# Run
uv run python -m ceramicraft_mcp_server.serve

# Lint & format
uv run ruff check .
uv run ruff format .

# Type check
uv run ty check src/

# Test
uv run pytest --cov=src/ceramicraft_mcp_server --cov-report=term-missing
```

## Configuration

All service URLs default to K8s cluster-internal addresses. Secrets (Zitadel credentials, DB passwords) are injected via Vault / ExternalSecret.

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_HOST` | Bind host | `0.0.0.0` |
| `MCP_SERVER_PORT` | Bind port | `8080` |
| `PRODUCT_MS_HTTP` | Product service URL | `http://product-ms-svc:8080` |
| `ORDER_MS_HTTP` | Order service URL | `http://order-ms-svc:8080` |
| `USER_MS_HTTP` | User service URL | `http://user-ms-svc:8080` |
| `COMMENT_MS_HTTP` | Comment service URL | `http://comment-ms-svc:8080` |
| `PAYMENT_MS_HTTP` | Payment service URL | `http://payment-ms-svc:8080` |
| `NOTIFICATION_MS_HTTP` | Notification service URL | `http://notification-ms-svc:8080` |
| `MCP_ZITADEL_ISSUER` | Zitadel issuer URL | *(set)* |
| `MCP_ZITADEL_JWKS_URL` | Zitadel JWKS endpoint | *(set)* |

