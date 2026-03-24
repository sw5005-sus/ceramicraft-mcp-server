# ceramicraft-mcp-server

MCP (Model Context Protocol) Server for the CeramiCraft multi-agent e-commerce platform.

## Overview

This service acts as the bridge between AI agents and CeramiCraft backend microservices. Agents communicate via the [MCP protocol](https://modelcontextprotocol.io), and the MCP Server translates tool calls into internal gRPC/HTTP requests to the appropriate microservices.

## Architecture

```
Agent (MCP Client)
    ↓ MCP Protocol (Streamable HTTP)
MCP Server (this service)
    ↓ gRPC / HTTP (cluster internal)
Backend Microservices (product, order, user, comment, payment, notification, log)
```

## Tools

### Public (no authentication required)
| Tool | Description |
|------|-------------|
| `search_products` | Search ceramic products by keyword |
| `get_product` | Get product details by ID |
| `list_product_categories` | List all product categories |
| `list_comments` | List comments for a product |

### Authenticated (requires user token)
| Tool | Description |
|------|-------------|
| `add_comment` | Add a comment to a product |
| `list_my_orders` | List authenticated user's orders |
| `get_order_detail` | Get order details |
| `get_my_profile` | Get user profile |
| `list_my_addresses` | List user's shipping addresses |
| `register_push_token` | Register FCM push token |

### Admin (requires admin role)
| Tool | Description |
|------|-------------|
| `query_audit_logs` | Query audit logs with filters |
| `verify_audit_chain` | Verify audit log hash chain integrity |

## Development

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup
```bash
uv sync
```

### Run locally
```bash
uv run ceramicraft-mcp
```

### Lint & Format
```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Type check
```bash
uv run ty check src/
```

### Test
```bash
uv run pytest
```

### Test with MCP Inspector
```bash
uv run ceramicraft-mcp &
npx -y @modelcontextprotocol/inspector
# Connect to http://localhost:8080/mcp
```

## Configuration

See [`.env.example`](.env.example) for all available environment variables.

## Docker

```bash
docker build -t ceramicraft-mcp-server .
docker run -p 8080:8080 ceramicraft-mcp-server
```
