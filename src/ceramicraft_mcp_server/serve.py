"""Entrypoint for the CeramiCraft MCP Server."""

import sys

from ceramicraft_mcp_server.app import create_mcp_server
from ceramicraft_mcp_server.config import get_settings


def main() -> None:
    """Start the MCP server with Streamable HTTP transport."""
    settings = get_settings()
    mcp = create_mcp_server(
        host=settings.MCP_SERVER_HOST,
        port=settings.MCP_SERVER_PORT,
    )
    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("\nMCP Server stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
