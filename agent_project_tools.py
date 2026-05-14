from typing import Any

from agent_framework import tool

from agent_request_context import require_current_oid
from project_tools import ProjectValidationError, create_project_for_user


def _tool_success(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _tool_failure(error: str) -> dict[str, Any]:
    return {"ok": False, "error": error}


@tool(
    name="create_project",
    description="Create a project for the authenticated user from request context",
)
def create_project_from_context_tool(
    name: str,
    tech_stack: list[str],
    urls: list[str],
    description: str,
    tags: list[str],
    summary: str,
) -> dict[str, Any]:
    try:
        oid = require_current_oid()
        project = create_project_for_user(
            oid=oid,
            name=name,
            tech_stack=tech_stack,
            urls=urls,
            description=description,
            tags=tags,
            summary=summary,
        )
        return _tool_success(project)
    except (ProjectValidationError, RuntimeError) as exc:
        return _tool_failure(str(exc))
