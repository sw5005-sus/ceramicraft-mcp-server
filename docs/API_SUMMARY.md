# CeramiCraft API Endpoints Summary

Generated from swagger.json / proto files in each microservice repo.

---

## product-ms (Go, MySQL, gRPC port 5001)

### Customer (C端)
| Method | Path | Description |
|--------|------|-------------|
| GET | /customer/cart | Get user's cart info |
| POST | /customer/cart/items | Create a cart item |
| DELETE | /customer/cart/items/:item_id | Delete a cart item |
| PUT | /customer/cart/items/:item_id | Update a cart item |
| GET | /customer/cart/price-estimate | Calculate order price |
| GET | /customer/cart/selected-num | Get number of selected items in cart |
| GET | /customer/product/{id} | Get product detail (customer) |
| GET | /customer/products | List products (customer) |

### Merchant (B端)
| Method | Path | Description |
|--------|------|-------------|
| POST | /merchant/images/upload-urls | Get presigned URL for image upload |
| GET | /merchant/product/{id} | Get product detail (merchant) |
| GET | /merchant/products | List products (merchant) |
| POST | /merchant/products | Add product |
| PATCH | /merchant/products/:id/status | Update product status (publish) |
| PATCH | /merchant/products/:id/stock | Update product stock |
| PUT | /merchant/products/{id} | Edit product info |

**Note:** All paths are prefixed with `/product-ms/v1` at the Traefik level.

---

## order-ms (Go, MySQL, gRPC port 5001)

### Customer
| Method | Path | Description |
|--------|------|-------------|
| POST | /customer/orders | Create order |
| POST | /customer/orders/list | List orders (customer) |
| GET | /customer/orders/{order_no} | Get order detail (customer) |
| PATCH | /customer/orders/{order_no}/confirm | Confirm receipt |

### Merchant
| Method | Path | Description |
|--------|------|-------------|
| GET | /merchant/order-stats | Get order statistics |
| POST | /merchant/orders/list | List orders (merchant) |
| GET | /merchant/orders/{order_no} | Get order detail (merchant) |
| GET | /merchant/orders/{order_no}/receive-info | Get order receiver info |
| PATCH | /merchant/orders/{order_no}/ship | Ship order |

**Note:** All paths are prefixed with `/order-ms/v1` at the Traefik level.

---

## user-ms (Go, MySQL, gRPC port 5001)

| Method | Path | Description |
|--------|------|-------------|
| GET | /oauth/v1/verify | Validate OAuth Token (used by Traefik forwardAuth) |
| POST | /user-ms/v1/customer/oauth-callback | Register via Zitadel |
| GET | /user-ms/v1/customer/users/self | Get user profile |
| PUT | /user-ms/v1/customer/users/self | Update user profile |
| GET | /user-ms/v1/customer/users/self/addresses | List addresses |
| POST | /user-ms/v1/customer/users/self/addresses | Create address |
| DELETE | /user-ms/v1/customer/users/self/addresses/{address_id} | Delete address |
| PUT | /user-ms/v1/customer/users/self/addresses/{address_id} | Update address |
| GET | /user-ms/v1/merchant/oauth-login | Admin OAuth login |
| GET | /user-ms/v1/merchant/login-callback | Admin login callback |
| GET | /user-ms/v1/merchant/oauth-logout | Admin logout |
| POST | /user-ms/v1/{client}/login | User login |
| POST | /user-ms/v1/{client}/logout | User logout |
| POST | /user-ms/v1/{client}/users | Register user |
| PUT | /user-ms/v1/{client}/users/activate | Activate user |

---

## comment-ms (Go, MySQL, gRPC port 5001)

### Customer
| Method | Path | Description |
|--------|------|-------------|
| POST | /comment-ms/v1/customer/reviews | Create review |
| GET | /comment-ms/v1/customer/reviews/product/{product_id} | Get reviews by product |
| GET | /comment-ms/v1/customer/reviews/user | Get reviews by user |
| POST | /comment-ms/v1/customer/reviews/{review_id}/like | Like a review |
| GET | /comment-ms/v1/users/{user_id}/reviews | Get all approved reviews by user (public) |

### Merchant
| Method | Path | Description |
|--------|------|-------------|
| POST | /comment-ms/v1/merchant/reviews/list | List reviews by product and stars |
| DELETE | /comment-ms/v1/merchant/reviews/{review_id} | Delete a review |
| PATCH | /comment-ms/v1/merchant/reviews/{review_id} | Pin a review |
| POST | /comment-ms/v1/merchant/reviews/{review_id}/replies | Reply to review |
| GET | /comment-ms/v1/reviews/status/{status} | List reviews by status (no auth) |
| POST | /comment-ms/v1/reviews/status | Update review status (no auth) |

---

## payment-ms (Go, MySQL, gRPC port 5001)

### Customer
| Method | Path | Description |
|--------|------|-------------|
| GET | /payment-ms/v1/customer/pay-accounts/self | Get user pay account |
| POST | /payment-ms/v1/customer/pay-accounts/self/top-ups | Top up account |

### Merchant
| Method | Path | Description |
|--------|------|-------------|
| GET | /payment-ms/v1/merchant/redeem-codes | Query redeem codes |
| POST | /payment-ms/v1/merchant/redeem-codes/generate | Generate redeem codes |

---

## notification-ms (Python, PostgreSQL, gRPC port 50051)

| Method | Path | Description |
|--------|------|-------------|
| GET | /notification-ms/v1/ping | Health check |
| POST | /notification-ms/v1/customer/push-token | Register FCM push token |

---

## log-ms (Python, PostgreSQL, gRPC port 50051)

| Method | Path | Description |
|--------|------|-------------|
| GET | /log-ms/v1/ping | Health check |
