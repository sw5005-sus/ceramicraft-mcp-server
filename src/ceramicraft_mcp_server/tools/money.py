"""Helpers for presenting money fields to MCP clients.

Product/order services store monetary values as integer cents. Tool results are
consumed by an LLM and should expose human-readable Singapore-dollar values
while keeping raw cents for traceability.
"""

from typing import Any


def with_display_money_fields(data: Any, money_keys: set[str]) -> Any:
    """Convert selected cent-denominated fields to display dollars recursively.

    For each numeric key listed in ``money_keys``, keep the raw value as
    ``<key>_cents``, replace ``<key>`` with dollars, and add
    ``<key>_display`` formatted for user-facing replies.
    """
    if isinstance(data, list):
        return [with_display_money_fields(item, money_keys) for item in data]

    if not isinstance(data, dict):
        return data

    normalized: dict[str, Any] = {}
    for key, value in data.items():
        if (
            key in money_keys
            and isinstance(value, int | float)
            and not isinstance(value, bool)
        ):
            dollars = round(value / 100, 2)
            normalized[key] = dollars
            normalized.setdefault(f"{key}_cents", value)
            normalized.setdefault(f"{key}_display", f"SGD {dollars:.2f}")
        else:
            normalized[key] = with_display_money_fields(value, money_keys)

    return normalized
