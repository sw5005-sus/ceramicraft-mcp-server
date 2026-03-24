"""User-related MCP tools (all require USER auth)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client


def _user_base() -> str:
    return get_settings().USER_MS_HTTP


def register_user_tools(mcp: FastMCP) -> None:
    """Register user tools on the MCP server."""

    @mcp.tool()
    async def get_my_profile(ctx: Context) -> dict[str, Any]:
        """Get the authenticated user's profile.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            User profile including name, email, phone, and avatar.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _user_base(),
            "GET",
            "/user-ms/v1/customer/users/self",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def update_my_profile(
        ctx: Context,
        name: str | None = None,
        phone: str | None = None,
        avatar: str | None = None,
    ) -> dict[str, Any]:
        """Update the authenticated user's profile.

        Args:
            ctx: MCP context (injected automatically).
            name: New display name.
            phone: New phone number.
            avatar: New avatar URL.

        Returns:
            Updated profile.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if phone is not None:
            body["phone"] = phone
        if avatar is not None:
            body["avatar"] = avatar

        return await client.call(
            _user_base(),
            "PUT",
            "/user-ms/v1/customer/users/self",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def list_my_addresses(ctx: Context) -> dict[str, Any]:
        """List the authenticated user's shipping addresses.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            A dict with a list of addresses.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _user_base(),
            "GET",
            "/user-ms/v1/customer/users/self/addresses",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def create_address(
        ctx: Context,
        name: str,
        phone: str,
        address: str,
        city: str = "",
        province: str = "",
        postal_code: str = "",
        is_default: bool = False,
    ) -> dict[str, Any]:
        """Create a new shipping address.

        Args:
            ctx: MCP context (injected automatically).
            name: Recipient name.
            phone: Recipient phone.
            address: Street address.
            city: City.
            province: Province/State.
            postal_code: Postal/ZIP code.
            is_default: Set as default address.

        Returns:
            Created address details.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _user_base(),
            "POST",
            "/user-ms/v1/customer/users/self/addresses",
            user_id=user.user_id_int,
            json_body={
                "name": name,
                "phone": phone,
                "address": address,
                "city": city,
                "province": province,
                "postal_code": postal_code,
                "is_default": is_default,
            },
        )

    @mcp.tool()
    async def update_address(
        ctx: Context,
        address_id: int,
        name: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        city: str | None = None,
        province: str | None = None,
        postal_code: str | None = None,
        is_default: bool | None = None,
    ) -> dict[str, Any]:
        """Update an existing shipping address.

        Args:
            ctx: MCP context (injected automatically).
            address_id: Address ID to update.
            name: New recipient name.
            phone: New recipient phone.
            address: New street address.
            city: New city.
            province: New province.
            postal_code: New postal code.
            is_default: Set as default address.

        Returns:
            Updated address details.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if phone is not None:
            body["phone"] = phone
        if address is not None:
            body["address"] = address
        if city is not None:
            body["city"] = city
        if province is not None:
            body["province"] = province
        if postal_code is not None:
            body["postal_code"] = postal_code
        if is_default is not None:
            body["is_default"] = is_default

        return await client.call(
            _user_base(),
            "PUT",
            f"/user-ms/v1/customer/users/self/addresses/{address_id}",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def delete_address(ctx: Context, address_id: int) -> dict[str, Any]:
        """Delete a shipping address.

        Args:
            ctx: MCP context (injected automatically).
            address_id: Address ID to delete.

        Returns:
            Deletion result.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            _user_base(),
            "DELETE",
            f"/user-ms/v1/customer/users/self/addresses/{address_id}",
            user_id=user.user_id_int,
        )
