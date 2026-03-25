# API Specs Version Tracking

Records which commit each spec was extracted from. Update this when re-pulling specs.

| Service | File | Source Repo | Commit | Date |
|---------|------|-------------|--------|------|
| product-ms | product-ms.json | ceramicraft-commodity-mservice | `41ed573` | 2026-03-19 |
| order-ms | order-ms.json | ceramicraft-order-mservice | `4623822` | 2026-03-21 |
| user-ms | user-ms.json | ceramicraft-user-mservice | `7bc7554` | 2026-03-21 |
| comment-ms | comment-ms.json | ceramicraft-comment-mservice | `7b3f8df` | 2026-03-21 |
| payment-ms | payment-ms.json | ceramicraft-payment-mservice | `32ea09c` | 2026-03-19 |
| log-ms | log-ms.proto | ceramicraft-log-mservice | `2cc75f2` | 2026-03-24 |
| notification-ms | notification-ms.proto | ceramicraft-notification-mservice | `ae2ba61` | 2026-03-24 |

## JSON API Specs (`json-apis/`)

Full Swagger/OpenAPI JSON files provided by Rocky (2026-03-25). These are the
authoritative API specs for cross-referencing MCP tool implementations.

- `json-apis/product-ms.json` — includes cart endpoints
- `json-apis/order-ms.json`
- `json-apis/comment-ms.json`
- `json-apis/user-ms.json`
- `json-apis/payment-ms.json`
- `json-apis/notification-ms.json`

## How to refresh

```bash
# Pull latest from each repo, then copy updated specs:
cd ceramicraft-commodity-mservice && git pull && cp server/docs/swagger.json ../ceramicraft-mcp-server/docs/api-specs/product-ms.json
# ... repeat for each service
# Then update the commit column in this table
```
