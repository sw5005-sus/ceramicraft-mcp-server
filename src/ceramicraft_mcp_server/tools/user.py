"""User-related MCP tools (all require USER auth)."""

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ceramicraft_mcp_server.auth import require_user
from ceramicraft_mcp_server.config import get_settings
from ceramicraft_mcp_server.http_client import get_http_client


def register_user_tools(mcp: FastMCP) -> None:
    """Register user tools on the MCP server."""

    @mcp.tool()
    async def get_my_profile(ctx: Context) -> dict[str, Any]:
        """Get the authenticated user's profile.

        Args:
            ctx: MCP context (injected automatically).

        Returns:
            User profile including name, email, and avatar.
        """
        user = await require_user(ctx)
        client = get_http_client()
        return await client.call(
            get_settings().USER_MS_HTTP,
            "GET",
            "/user-ms/v1/customer/users/self",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def update_my_profile(
        ctx: Context,
        name: str | None = None,
        email: str | None = None,
        avatar: str | None = None,
    ) -> dict[str, Any]:
        """Update the authenticated user's profile.

        Args:
            ctx: MCP context (injected automatically).
            name: New display name.
            email: New email address.
            avatar: New avatar URL.

        Returns:
            Updated profile.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if email is not None:
            body["email"] = email
        if avatar is not None:
            body["avatar"] = avatar

        return await client.call(
            get_settings().USER_MS_HTTP,
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
            get_settings().USER_MS_HTTP,
            "GET",
            "/user-ms/v1/customer/users/self/addresses",
            user_id=user.user_id_int,
        )

    @mcp.tool()
    async def create_address(
        ctx: Context,
        first_name: str,
        last_name: str,
        contact_phone: str,
        detail: str,
        city: str = "",
        province: str = "",
        country: str = "",
        zip_code: str = "",
        is_default: bool = False,
    ) -> dict[str, Any]:
        """Create a new shipping address.

        Args:
            ctx: MCP context (injected automatically).
            first_name: Recipient first name.
            last_name: Recipient last name.
            contact_phone: Recipient phone number.
            detail: Street address / address detail.
            city: City.
            province: Province/State.
            country: Country.
            zip_code: Postal/ZIP code.
            is_default: Set as default address.

        Returns:
            Created address details.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "contact_phone": contact_phone,
            "detail": detail,
            "is_default": is_default,
        }
        if city:
            body["city"] = city
        if province:
            body["province"] = province
        if country:
            body["country"] = country
        if zip_code:
            body["zip_code"] = zip_code

        return await client.call(
            get_settings().USER_MS_HTTP,
            "POST",
            "/user-ms/v1/customer/users/self/addresses",
            user_id=user.user_id_int,
            json_body=body,
        )

    @mcp.tool()
    async def update_address(
        ctx: Context,
        address_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        contact_phone: str | None = None,
        detail: str | None = None,
        city: str | None = None,
        province: str | None = None,
        country: str | None = None,
        zip_code: str | None = None,
        is_default: bool | None = None,
    ) -> dict[str, Any]:
        """Update an existing shipping address.

        Args:
            ctx: MCP context (injected automatically).
            address_id: Address ID to update.
            first_name: New recipient first name.
            last_name: New recipient last name.
            contact_phone: New phone number.
            detail: New street address.
            city: New city.
            province: New province.
            country: New country.
            zip_code: New postal code.
            is_default: Set as default address.

        Returns:
            Updated address details.
        """
        user = await require_user(ctx)
        client = get_http_client()
        body: dict[str, Any] = {}
        if first_name is not None:
            body["first_name"] = first_name
        if last_name is not None:
            body["last_name"] = last_name
        if contact_phone is not None:
            body["contact_phone"] = contact_phone
        if detail is not None:
            body["detail"] = detail
        if city is not None:
            body["city"] = city
        if province is not None:
            body["province"] = province
        if country is not None:
            body["country"] = country
        if zip_code is not None:
            body["zip_code"] = zip_code
        if is_default is not None:
            body["is_default"] = is_default

        return await client.call(
            get_settings().USER_MS_HTTP,
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
            get_settings().USER_MS_HTTP,
            "DELETE",
            f"/user-ms/v1/customer/users/self/addresses/{address_id}",
            user_id=user.user_id_int,
        )
