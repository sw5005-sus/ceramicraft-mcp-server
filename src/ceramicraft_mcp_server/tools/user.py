"""User-related MCP tools (all require authentication)."""

from mcp.server.fastmcp import Context, FastMCP


def register_user_tools(mcp: FastMCP) -> None:
    """Register user tools on the MCP server."""

    @mcp.tool()
    async def get_my_profile(ctx: Context) -> dict:
        """Get the authenticated user's profile.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            User profile including name, email, and addresses.
        """
        # TODO: Extract user_id from ctx, call user-ms HTTP/gRPC
        _ = ctx
        return {"user_id": "", "name": "", "email": ""}

    @mcp.tool()
    async def list_my_addresses(ctx: Context) -> dict:
        """List the authenticated user's shipping addresses.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            A dict with a list of addresses.
        """
        # TODO: Extract user_id from ctx, call user-ms
        _ = ctx
        return {"addresses": []}
