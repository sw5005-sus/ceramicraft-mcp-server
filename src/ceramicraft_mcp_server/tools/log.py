"""Audit log MCP tools (internal/admin use)."""

from mcp.server.fastmcp import Context, FastMCP


def register_log_tools(mcp: FastMCP) -> None:
    """Register audit log tools on the MCP server."""

    @mcp.tool()
    async def query_audit_logs(
        ctx: Context,
        actor_id: int | None = None,
        service: str | None = None,
        role: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Query audit logs with optional filters (admin only).

        Args:
            ctx: MCP context (injected automatically).
            actor_id: Filter by actor ID.
            service: Filter by service name.
            role: Filter by actor role.
            limit: Maximum number of logs to return.
            offset: Pagination offset.

        Returns:
            A dict with audit log entries and total count.
        """
        # TODO: Verify admin role from ctx, call log-ms gRPC QueryAuditLogs
        _ = ctx
        return {"logs": [], "total": 0}

    @mcp.tool()
    async def verify_audit_chain(
        ctx: Context,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """Verify the integrity of the audit log hash chain (admin only).

        Args:
            ctx: MCP context (injected automatically).
            start_time: Start time filter (ISO 8601).
            end_time: End time filter (ISO 8601).

        Returns:
            Verification result including validity status.
        """
        # TODO: Verify admin role from ctx, call log-ms gRPC VerifyAuditLogChain
        _ = ctx
        return {"is_valid": True, "message": ""}
