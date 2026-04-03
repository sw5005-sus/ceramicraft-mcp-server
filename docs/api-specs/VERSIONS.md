# API Specs Version Tracking

Records which commit each spec was extracted from. Update this when re-pulling specs.

| Service | File | Source Repo | Commit | Date |
|---------|------|-------------|--------|------|
| product-ms | product-ms.json | ceramicraft-commodity-mservice | `41ed573` | 2026-03-19 |
| order-ms | order-ms.json | ceramicraft-order-mservice | `4623822` | 2026-03-21 |
| user-ms | user-ms.json | ceramicraft-user-mservice | `7bc7554` | 2026-03-21 |
| comment-ms | comment-ms.json | ceramicraft-comment-mservice | `7b3f8df` | 2026-03-21 |
| payment-ms | payment-ms.json | ceramicraft-payment-mservice | `32ea09c` | 2026-03-19 |
| notification-ms | notification-ms.json | ceramicraft-notification-mservice | `6712e0f` | 2026-04-03 |

All specs are full Swagger/OpenAPI JSON files (2-space indent).
Product spec includes cart endpoints.

## How to refresh

```bash
# Pull latest from each repo, then copy updated specs:
cd ceramicraft-commodity-mservice && git pull && cp server/docs/swagger.json ../ceramicraft-mcp-server/docs/api-specs/product-ms.json
# ... repeat for each service
# Then update the commit column in this table
```
