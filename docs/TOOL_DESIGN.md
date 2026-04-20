# MCP Server — Tool Design & Auth Plan

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     AI Agents (MCP Clients)              │
│                                                          │
│  Product Agent    Search Agent    Customer Support Agent  │
│  Product Review   Comment Review  AIOps Monitor          │
└──────────────────────┬───────────────────────────────────┘
                       │ MCP Protocol (Streamable HTTP)
                       │ Bearer Token (Zitadel JWT)
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   MCP Server (this service)               │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ JWT Verifier │  │ Role Checker │  │ Tool Registry  │  │
│  │ (JWKS)      │  │ (per-tool)   │  │ (FastMCP)      │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                          │
│  Internal calls: HTTP with X-Original-User-ID header     │
└───────┬──────────┬──────────┬──────────┬─────────────────┘
        │          │          │          │
   product-ms  order-ms  comment-ms  notification-ms
   payment-ms  user-ms
```

## 2. Communication Strategy

### MCP Server → Go Services (product/order/user/comment/payment)

**Protocol: Internal HTTP** (not gRPC)

Reason: Go services expose HTTP REST APIs with Swagger docs. Their gRPC layer
is primarily for inter-Go-service calls and not all endpoints are mirrored in
gRPC. HTTP is the most complete interface.

The MCP Server calls Go services at their cluster-internal addresses:
```
http://product-ms-svc:8080/product-ms/v1/customer/products
http://order-ms-svc:8080/order-ms/v1/customer/orders
...
```

**Authentication injection**: Go services use `AuthMiddleware` which reads user
identity from `X-Original-User-ID` header (set by Traefik forwardAuth in
production). When MCP Server calls on behalf of a user, it verifies the agent's
JWT, extracts the internal user ID from Zitadel user metadata
(`urn:zitadel:iam:user:metadata.local_userid`, base64-encoded), and injects
this header into internal HTTP calls. Falls back to `sub` if metadata is absent.

## 3. Auth Model

### Three Auth Levels

```
┌─────────────────────────────────────────────────────────┐
│  Level 0: PUBLIC — No token needed                       │
│  Anyone can call. Used by Search Agent for browsing.     │
├─────────────────────────────────────────────────────────┤
│  Level 1: USER — Valid Zitadel JWT required              │
│  Token must contain `local_userid` in Zitadel user       │
│  metadata. MCP Server extracts internal user_id and      │
│  passes it to backend via X-Original-User-ID header.     │
│  Falls back to `sub` if metadata is absent.              │
├─────────────────────────────────────────────────────────┤
│  Level 2: ADMIN — Valid JWT + per-tool role check         │
│  Roles: merchant_admin, product_auditor, product_editor  │
│  Each tool specifies which roles are allowed.            │
│  Token must contain role in                              │
│  `urn:zitadel:iam:org:project:roles` claim.              │
│  Used by Product Agent, Comment Review Agent, etc.       │
└─────────────────────────────────────────────────────────┘
```

### How Auth Flows Per Agent Type

| Agent | Auth Level | Identity Source | Notes |
|-------|-----------|-----------------|-------|
| Search Intention Agent | PUBLIC | None | Browses products anonymously |
| Customer Support Agent | USER | End-user JWT | Acts on behalf of logged-in customer |
| Product Agent | ADMIN (`merchant_admin`, `product_editor`) | Service Account JWT | Creates/edits products |
| Product Review Agent | ADMIN (`merchant_admin`, `product_auditor`) | Service Account JWT | Reviews product listings |
| Comment Review Agent | ADMIN (`merchant_admin`) | Service Account JWT | Moderates reviews |
| AIOps Monitoring Agent | ADMIN (`merchant_admin`) | Service Account JWT | Reads system metrics/logs |

### Auth Implementation

```python
# In each tool function:

# PUBLIC — no check
@mcp.tool()
async def search_products(keyword: str, ...) -> dict:
    ...

# USER — verify token, extract user_id
@mcp.tool()
async def list_my_orders(ctx: Context) -> dict:
    user = await require_user(ctx)  # raises ToolError if no valid token
    response = await http_client.get(
        f"{ORDER_MS}/order-ms/v1/customer/orders/list",
        headers={"X-Original-User-ID": str(user.user_id)}
    )
    ...

# ADMIN — verify token + check specific role
@mcp.tool()
async def delete_review(ctx: Context, review_id: str) -> dict:
    user = await require_role(ctx, ROLE_MERCHANT_ADMIN)  # only merchant_admin
    ...

@mcp.tool()
async def create_product(ctx: Context, ...) -> dict:
    user = await require_role(ctx, ROLE_PRODUCT_WRITE)  # merchant_admin or product_editor
    ...
```

### Token Passing

MCP Clients (agents) pass the Zitadel JWT in the MCP request. Two scenarios:

1. **Agent acting on behalf of user**: Agent receives user's JWT from the
   frontend and includes it in MCP calls. MCP Server verifies and extracts
   the internal user ID from `urn:zitadel:iam:user:metadata.local_userid`
   (base64-encoded). This is the MySQL auto-increment ID written by user-ms
   during OAuth registration. Falls back to `sub` if metadata is absent.

2. **Agent acting autonomously**: Agent uses its own Service Account
   credentials (client_credentials grant) to obtain a JWT from Zitadel.
   MCP Server verifies and recognizes it as a service account.

## 4. Tool Catalog

### 4.1 Product Tools

Used by: **Search Intention Agent**, **Customer Support Agent**, **Product Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `search_products` | PUBLIC | `GET /product-ms/v1/customer/products?keyword=...` | Search Agent: semantic search → keyword extraction → call this |
| `get_product` | PUBLIC | `GET /product-ms/v1/customer/product/{id}` | Support Agent: show product details to user |
| `create_product` | ADMIN (`merchant_admin`, `product_editor`) | `POST /product-ms/v1/merchant/products` | Product Agent: auto-generate listing |
| `update_product` | ADMIN (`merchant_admin`, `product_editor`) | `PUT /product-ms/v1/merchant/products/{id}` | Product Agent: edit descriptions |
| `update_product_status` | ADMIN (`merchant_admin`, `product_auditor`) | `PATCH /product-ms/v1/merchant/products/{id}/status` | Product Review Agent: publish/unpublish after review |
| `update_product_stock` | ADMIN (`merchant_admin`, `product_editor`) | `PATCH /product-ms/v1/merchant/products/{id}/stock` | Product Agent: inventory management |
| `get_merchant_product` | ADMIN (all) | `GET /product-ms/v1/merchant/product/{id}` | Product Review Agent: get full merchant-view details |
| `list_merchant_products` | ADMIN (all) | `GET /product-ms/v1/merchant/products` | Product Review Agent: list products pending review |
| `get_image_upload_url` | ADMIN (`merchant_admin`, `product_editor`) | `POST /product-ms/v1/merchant/images/upload-urls` | Product Agent: upload generated images |

### 4.2 Cart Tools

Used by: **Customer Support Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `get_cart` | USER | `GET /product-ms/v1/customer/cart` | Support Agent: view user's cart |
| `add_to_cart` | USER | `POST /product-ms/v1/customer/cart/items` | Support Agent: help user add items |
| `update_cart_item` | USER | `PUT /product-ms/v1/customer/cart/items/{id}` | Support Agent: change quantity |
| `remove_cart_item` | USER | `DELETE /product-ms/v1/customer/cart/items/{id}` | Support Agent: remove items |
| `estimate_cart_price` | USER | `GET /product-ms/v1/customer/cart/price-estimate` | Support Agent: show total before checkout |

### 4.3 Order Tools

Used by: **Customer Support Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `create_order` | USER | `POST /order-ms/v1/customer/orders` | Support Agent: help user place order |
| `list_my_orders` | USER | `POST /order-ms/v1/customer/orders/list` | Support Agent: show order history |
| `get_order_detail` | USER | `GET /order-ms/v1/customer/orders/{order_no}` | Support Agent: order status inquiry |
| `confirm_receipt` | USER | `PATCH /order-ms/v1/customer/orders/{order_no}/confirm` | Support Agent: confirm delivery |
| `get_order_stats` | ADMIN (`merchant_admin`) | `GET /order-ms/v1/merchant/order-stats` | AIOps Agent: dashboard metrics |
| `list_merchant_orders` | ADMIN (`merchant_admin`) | `POST /order-ms/v1/merchant/orders/list` | AIOps Agent: order monitoring |
| `get_merchant_order_detail` | ADMIN (`merchant_admin`) | `GET /order-ms/v1/merchant/orders/{order_no}` | AIOps Agent: detailed investigation |
| `ship_order` | ADMIN (`merchant_admin`) | `PATCH /order-ms/v1/merchant/orders/{order_no}/ship` | (future) auto-fulfillment |

### 4.4 Comment/Review Tools

Used by: **Comment Review Agent**, **Customer Support Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `list_product_reviews` | USER | `GET /comment-ms/v1/customer/reviews/product/{id}` | Support Agent: show reviews; Comment Review Agent: fetch for analysis |
| `get_user_reviews` | USER | `GET /comment-ms/v1/customer/reviews/user` | Support Agent: show user's own reviews |
| `create_review` | USER | `POST /comment-ms/v1/customer/reviews` | Support Agent: help user post review |
| `like_review` | USER | `POST /comment-ms/v1/customer/reviews/{id}/like` | Support Agent: like on behalf of user |
| `list_reviews_by_user_id` | PUBLIC | `GET /comment-ms/v1/users/{user_id}/reviews` | Support Agent / Review Moderation Agent: get all approved reviews by a user (sorted by created_at desc) |
| `list_reviews_admin` | ADMIN (`merchant_admin`) | `POST /comment-ms/v1/merchant/reviews/list` | Merchant: list reviews filtered by product_id and stars (dashboard view) |
| `delete_review` | ADMIN (`merchant_admin`) | `DELETE /comment-ms/v1/merchant/reviews/{id}` | Merchant: remove a review |
| `pin_review` | ADMIN (`merchant_admin`) | `PATCH /comment-ms/v1/merchant/reviews/{id}` | Merchant: pin high-quality reviews |
| `reply_to_review` | ADMIN (`merchant_admin`) | `POST /comment-ms/v1/merchant/reviews/{id}/replies` | Merchant: auto-draft or post reply |
| `list_reviews_by_status` | INTERNAL M2M (no auth) | `GET /comment-ms/v1/reviews/status/{status}` | Review Moderation Agent: batch-fetch reviews by moderation status (pending, processing, approved, hidden, rejected) |
| `update_review_status` | INTERNAL M2M (no auth) | `POST /comment-ms/v1/reviews/status` | Review Moderation Agent: update review status, rating (stars), and flags (is_mismatch, is_harmful, auto_flag); audit logged on server |

### 4.5 User Tools

Used by: **Customer Support Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `get_my_profile` | USER | `GET /user-ms/v1/customer/users/self` | Support Agent: greet user by name, verify identity |
| `update_my_profile` | USER | `PUT /user-ms/v1/customer/users/self` | Support Agent: help update profile |
| `list_my_addresses` | USER | `GET /user-ms/v1/customer/users/self/addresses` | Support Agent: show addresses for order |
| `create_address` | USER | `POST /user-ms/v1/customer/users/self/addresses` | Support Agent: help add address |
| `update_address` | USER | `PUT /user-ms/v1/customer/users/self/addresses/{id}` | Support Agent: edit address |
| `delete_address` | USER | `DELETE /user-ms/v1/customer/users/self/addresses/{id}` | Support Agent: remove address |

### 4.6 Payment Tools

Used by: **Customer Support Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `get_pay_account` | USER | `GET /payment-ms/v1/customer/pay-accounts/self` | Support Agent: check balance |
| `top_up_account` | USER | `POST /payment-ms/v1/customer/pay-accounts/self/top-ups` | Support Agent: help top up |
| `list_redeem_codes` | ADMIN (`merchant_admin`) | `GET /payment-ms/v1/merchant/redeem-codes` | AIOps Agent: monitor promotions |
| `generate_redeem_codes` | ADMIN (`merchant_admin`) | `POST /payment-ms/v1/merchant/redeem-codes/generate` | (future) auto-promotion |

### 4.7 Notification Tools

Used by: **Customer Support Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `register_push_token` | USER | `POST /notification-ms/v1/customer/push-token` header: `X-Original-User-ID`, body: `{device_id, fcm_token}` | Support Agent: help register device |

## 5. Tool Count Summary

| Category | PUBLIC | USER | ADMIN | INTERNAL M2M | Total |
|----------|--------|------|-------|--------------|-------|
| Product | 2 | 0 | 7 | 0 | 9 |
| Cart | 0 | 5 | 0 | 0 | 5 |
| Order | 0 | 4 | 4 | 0 | 8 |
| Comment/Review | 0 | 4 | 4 | 3 | 11 |
| User | 0 | 6 | 0 | 0 | 6 |
| Payment | 0 | 2 | 2 | 0 | 4 |
| Notification | 0 | 1 | 0 | 0 | 1 |
| **Total** | **2** | **22** | **17** | **3** | **44** |

## 6. Agent → Tool Mapping

| Agent | Primary Tools | Auth Level |
|-------|--------------|------------|
| **Search Intention Agent** | search_products, get_product | PUBLIC |
| **Customer Support Agent** | All USER tools + PUBLIC product/review tools | USER |
| **Product Agent** | create/update/get_merchant product tools, get_image_upload_url | `merchant_admin`, `product_editor` |
| **Product Review Agent** | list/get_merchant products, update_product_status | `merchant_admin`, `product_auditor` |
| **Comment Review Agent** | list/delete/pin/reply reviews | `merchant_admin` |
| **AIOps Monitoring Agent** | get_order_stats, list_merchant_orders | `merchant_admin` |

## 7. Internal HTTP Client Design

```python
class InternalHTTPClient:
    """Makes authenticated HTTP calls to Go backend services."""

    async def call(
        self,
        service_base: str,    # e.g. "http://product-ms-svc:8080"
        method: str,          # GET, POST, PUT, PATCH, DELETE
        path: str,            # e.g. "/product-ms/v1/customer/products"
        user_id: int | None,  # injected as X-Original-User-ID
        params: dict | None,
        body: dict | None,
    ) -> dict:
        headers = {}
        if user_id is not None:
            headers["X-Original-User-ID"] = str(user_id)
        ...
```

## 8. Implementation Priority

### Phase 1 — Core (Customer Support + Search) ✅
1. Internal HTTP client with X-Original-User-ID injection
2. Product tools (PUBLIC): search, get
3. Cart tools (USER)
4. Order tools (USER): list, detail
5. User tools (USER): profile, addresses
6. Auth helpers: `require_user()`, `require_admin()`

### Phase 2 — Admin (Product + Comment Review) ✅
7. Product merchant tools (ADMIN)
8. Comment review tools (ADMIN)
9. Payment tools (USER + ADMIN)
10. Notification: register_push_token (USER)
