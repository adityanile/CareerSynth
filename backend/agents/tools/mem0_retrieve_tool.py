from __future__ import annotations

from typing import Any

from agent_framework import tool

from agents.context import require_current_oid
from core.settings import get_settings
from agents.tools.tool_response import format_tool_failure


def _tool_success(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _tool_failure(tool_name: str, error: str) -> str:
    return format_tool_failure(tool_name=tool_name, error=error)


@tool(
    name="retrieve",
    description=(
        "Search mem0 memory for the authenticated user. "
        "Use this before answering user-specific preference/history questions."
    ),
)
def retrieve_from_mem0_tool(
    query: str = "",
) -> dict[str, Any] | str:
    tool_name = "retrieve"
    try:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query is required")

        settings = get_settings()
        if not settings.mem0_api_key:
            raise RuntimeError("MEM0_API_KEY is not configured")

        # Lazy import keeps startup/tests resilient when mem0 client is unavailable.
        from mem0 import MemoryClient

        oid = require_current_oid()
        filters: dict[str, Any] = {"user_id": oid}

        client = MemoryClient(api_key=settings.mem0_api_key)
        results = client.search(normalized_query, filters=filters)
        return _tool_success({"items": results})
    except Exception as exc:
        return _tool_failure(tool_name, str(exc))
