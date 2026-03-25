# MCP Server — Tool Design & Auth Plan

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     AI Agents (MCP Clients)              │
│                                                          │
│  Product Agent    Search Agent    Customer Support Agent  │
│  Product Review   Comment Review  AI Security Agent      │
│  AIOps Monitor                                           │
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
│                  gRPC for Python services                 │
└───────┬──────────┬──────────┬──────────┬─────────────────┘
        │          │          │          │
   product-ms  order-ms  comment-ms   log-ms
   payment-ms  user-ms   notification-ms
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
JWT, extracts `sub` (user ID), and injects this header into internal HTTP calls.

### MCP Server → Python Services (log/notification)

**Protocol: gRPC** (port 50051)

These services only expose gRPC for business logic. HTTP is only for health checks.

## 3. Auth Model

### Three Auth Levels

```
┌─────────────────────────────────────────────────────────┐
│  Level 0: PUBLIC — No token needed                       │
│  Anyone can call. Used by Search Agent for browsing.     │
├─────────────────────────────────────────────────────────┤
│  Level 1: USER — Valid Zitadel JWT required              │
│  Token must have valid `sub`. MCP Server extracts        │
│  user_id and passes it to backend via                    │
│  X-Original-User-ID header.                              │
├─────────────────────────────────────────────────────────┤
│  Level 2: ADMIN — Valid JWT + admin/merchant role        │
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
| Product Agent | ADMIN | Merchant JWT | Creates/edits products |
| Product Review Agent | ADMIN | Merchant JWT | Reviews product listings |
| Comment Review Agent | ADMIN | Merchant/System JWT | Moderates reviews |
| AI Security Agent | ADMIN | Service Account JWT | Reads logs, flags users |
| AIOps Monitoring Agent | ADMIN | Service Account JWT | Reads system metrics/logs |

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

# ADMIN — verify token + check role
@mcp.tool()
async def delete_review(ctx: Context, review_id: str) -> dict:
    user = await require_admin(ctx)  # raises ToolError if not admin
    ...
```

### Token Passing

MCP Clients (agents) pass the Zitadel JWT in the MCP request. Two scenarios:

1. **Agent acting on behalf of user**: Agent receives user's JWT from the
   frontend and includes it in MCP calls. MCP Server verifies and extracts
   `sub` as user_id.

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
| `create_product` | ADMIN | `POST /product-ms/v1/merchant/products` | Product Agent: auto-generate listing |
| `update_product` | ADMIN | `PUT /product-ms/v1/merchant/products/{id}` | Product Agent: edit descriptions |
| `update_product_status` | ADMIN | `PATCH /product-ms/v1/merchant/products/{id}/status` | Product Review Agent: publish/unpublish after review |
| `update_product_stock` | ADMIN | `PATCH /product-ms/v1/merchant/products/{id}/stock` | Product Agent: inventory management |
| `get_merchant_product` | ADMIN | `GET /product-ms/v1/merchant/product/{id}` | Product Review Agent: get full merchant-view details |
| `list_merchant_products` | ADMIN | `GET /product-ms/v1/merchant/products` | Product Review Agent: list products pending review |
| `get_image_upload_url` | ADMIN | `POST /product-ms/v1/merchant/images/upload-urls` | Product Agent: upload generated images |

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
| `get_order_stats` | ADMIN | `GET /order-ms/v1/merchant/order-stats` | AIOps Agent: dashboard metrics |
| `list_merchant_orders` | ADMIN | `POST /order-ms/v1/merchant/orders/list` | AIOps Agent: order monitoring |
| `get_merchant_order_detail` | ADMIN | `GET /order-ms/v1/merchant/orders/{order_no}` | AIOps Agent: detailed investigation |
| `ship_order` | ADMIN | `PATCH /order-ms/v1/merchant/orders/{order_no}/ship` | (future) auto-fulfillment |

### 4.4 Comment/Review Tools

Used by: **Comment Review Agent**, **Customer Support Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `list_product_reviews` | PUBLIC | `GET /comment-ms/v1/customer/reviews/product/{id}` | Support Agent: show reviews; Comment Review Agent: fetch for analysis |
| `get_user_reviews` | USER | `GET /comment-ms/v1/customer/reviews/user` | Support Agent: show user's own reviews |
| `create_review` | USER | `POST /comment-ms/v1/customer/reviews` | Support Agent: help user post review |
| `like_review` | USER | `POST /comment-ms/v1/customer/reviews/{id}/like` | Support Agent: like on behalf of user |
| `list_reviews_admin` | ADMIN | `POST /comment-ms/v1/merchant/reviews/list` | Comment Review Agent: list reviews for moderation |
| `delete_review` | ADMIN | `DELETE /comment-ms/v1/merchant/reviews/{id}` | Comment Review Agent: remove violating content |
| `pin_review` | ADMIN | `PATCH /comment-ms/v1/merchant/reviews/{id}` | Comment Review Agent: pin high-quality reviews |
| `reply_to_review` | ADMIN | `POST /comment-ms/v1/merchant/reviews/{id}/replies` | Comment Review Agent: auto-draft merchant reply |

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
| `list_redeem_codes` | ADMIN | `GET /payment-ms/v1/merchant/redeem-codes` | AIOps Agent: monitor promotions |
| `generate_redeem_codes` | ADMIN | `POST /payment-ms/v1/merchant/redeem-codes/generate` | (future) auto-promotion |

### 4.7 Notification Tools

Used by: **Comment Review Agent**, **AI Security Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `send_push_notification` | ADMIN | gRPC `SendUserPush` | Comment Review Agent: notify user of moderation result; Security Agent: alert user |
| `register_push_token` | USER | `POST /notification-ms/v1/push-token` body: `{user_id, device_id, fcm_token}` | Support Agent: help register device |

### 4.8 Audit Log Tools

Used by: **AI Security Agent**, **AIOps Monitoring Agent**

| Tool | Auth | Backend Call | Agent Use Case |
|------|------|-------------|----------------|
| `record_audit_log` | ADMIN | gRPC `RecordAuditLog` | Security Agent: log security events |
| `query_audit_logs` | ADMIN | gRPC `QueryAuditLogs` | Security Agent: analyze patterns; AIOps: monitoring |
| `verify_audit_chain` | ADMIN | gRPC `VerifyAuditLogChain` | Security Agent: tamper detection |

## 5. Tool Count Summary

| Category | PUBLIC | USER | ADMIN | Total |
|----------|--------|------|-------|-------|
| Product | 2 | 0 | 7 | 9 |
| Cart | 0 | 5 | 0 | 5 |
| Order | 0 | 4 | 4 | 8 |
| Comment/Review | 1 | 3 | 4 | 8 |
| User | 0 | 6 | 0 | 6 |
| Payment | 0 | 2 | 2 | 4 |
| Notification | 0 | 1 | 1 | 2 |
| Audit Log | 0 | 0 | 3 | 3 |
| **Total** | **3** | **21** | **21** | **45** |

## 6. Agent → Tool Mapping

| Agent | Primary Tools | Auth Level |
|-------|--------------|------------|
| **Search Intention Agent** | search_products, get_product | PUBLIC |
| **Customer Support Agent** | All USER tools + PUBLIC product/review tools | USER |
| **Product Agent** | create/update/get_merchant product tools, get_image_upload_url | ADMIN |
| **Product Review Agent** | list/get_merchant products, update_product_status | ADMIN |
| **Comment Review Agent** | list/delete/pin/reply reviews, send_push_notification | ADMIN |
| **AI Security Agent** | record/query/verify audit logs, send_push_notification | ADMIN |
| **AIOps Monitoring Agent** | query_audit_logs, get_order_stats, list_merchant_orders | ADMIN |

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

### Phase 1 — Core (Customer Support + Search)
1. Internal HTTP client with X-Original-User-ID injection
2. Product tools (PUBLIC): search, get, categories
3. Cart tools (USER)
4. Order tools (USER): list, detail
5. User tools (USER): profile, addresses
6. Auth helpers: `require_user()`, `require_admin()`

### Phase 2 — Admin (Product + Comment Review)
7. Product merchant tools (ADMIN)
8. Comment review tools (ADMIN)
9. gRPC client for notification-ms

### Phase 3 — Security & Ops
10. gRPC client for log-ms
11. Audit log tools (ADMIN)
12. Payment tools
