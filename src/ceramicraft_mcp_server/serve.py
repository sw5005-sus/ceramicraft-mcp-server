"""Entrypoint for the CeramiCraft MCP Server."""

from ceramicraft_mcp_server.app import create_mcp_server
from ceramicraft_mcp_server.config import get_settings


def main() -> None:
    """Start the MCP server with Streamable HTTP transport."""
    settings = get_settings()
    mcp = create_mcp_server()
    mcp.run(
        transport="streamable-http",
        host=settings.MCP_SERVER_HOST,
        port=settings.MCP_SERVER_PORT,
    )


if __name__ == "__main__":
    main()
