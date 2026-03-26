"""Entrypoint for the CeramiCraft MCP Server."""

import sys

import dttb

from ceramicraft_mcp_server.app import create_mcp_server
from ceramicraft_mcp_server.config import get_settings

# Apply dttb tracebacks for timestamps on exceptions
dttb.apply()


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
