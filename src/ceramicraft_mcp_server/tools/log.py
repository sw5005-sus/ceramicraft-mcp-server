"""Audit log MCP tools (all require ADMIN auth).

Uses gRPC to call log-ms AuditLogService.
"""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_admin


def register_log_tools(mcp: FastMCP) -> None:
    """Register audit log tools on the MCP server."""

    @mcp.tool()
    async def record_audit_log(
        ctx: Context,
        service: str,
        actor_id: int,
        role: str,
        description: str,
        occurred_at: str = "",
    ) -> dict[str, Any]:
        """Record an audit log entry. Requires admin role.

        Args:
            ctx: MCP context (injected automatically).
            service: Name of the calling service (e.g. "ai-security-agent").
            actor_id: ID of the actor.
            role: Role of the actor (MERCHANT, CUSTOMER, SYSTEM).
            description: Description of the action.
            occurred_at: Event time as ISO 8601 string. Defaults to now.

        Returns:
            Result with event_id of the created log entry.
        """
        await require_admin(ctx)
        # TODO: Replace with gRPC call to log-ms RecordAuditLog
        return {
            "success": False,
            "message": "gRPC client not yet implemented.",
            "service": service,
            "actor_id": actor_id,
            "role": role,
            "description": description,
        }

    @mcp.tool()
    async def query_audit_logs(
        ctx: Context,
        actor_id: int | None = None,
        service: str | None = None,
        role: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        occurred_at_start: str | None = None,
        occurred_at_end: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Query audit logs with optional filters. Requires admin role.

        Args:
            ctx: MCP context (injected automatically).
            actor_id: Filter by actor ID.
            service: Filter by service name.
            role: Filter by actor role.
            start_time: Filter by log write time start (ISO 8601).
            end_time: Filter by log write time end (ISO 8601).
            occurred_at_start: Filter by event time start (ISO 8601).
            occurred_at_end: Filter by event time end (ISO 8601).
            limit: Maximum number of logs to return.
            offset: Pagination offset.

        Returns:
            A dict with audit log entries and total count.
        """
        await require_admin(ctx)
        # TODO: Replace with gRPC call to log-ms QueryAuditLogs
        return {
            "success": False,
            "message": "gRPC client not yet implemented.",
            "logs": [],
            "total_count": 0,
        }

    @mcp.tool()
    async def verify_audit_chain(
        ctx: Context,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Verify the integrity of the audit log hash chain. Requires admin role.

        Args:
            ctx: MCP context (injected automatically).
            start_time: Start time filter (ISO 8601).
            end_time: End time filter (ISO 8601).

        Returns:
            Verification result including validity status and failure details.
        """
        await require_admin(ctx)
        # TODO: Replace with gRPC call to log-ms VerifyAuditLogChain
        return {
            "success": False,
            "message": "gRPC client not yet implemented.",
            "is_valid": False,
            "failed_log_id": "",
        }
