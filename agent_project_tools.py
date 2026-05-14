import json
from typing import Any

from agent_framework import tool

from agent_request_context import require_current_oid
from project_tools import create_project_for_user, list_projects_for_user
from tool_response import format_tool_failure


def _tool_success(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _tool_failure(tool_name: str, error: str) -> str:
    return format_tool_failure(tool_name=tool_name, error=error)


def _coerce_string_list(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    text = value.strip()
    if not text:
        return []
    if text.startswith("["):
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return [part.strip() for part in text.split(",") if part.strip()]


@tool(
    name="create_project",
    description="Create a project for the authenticated user from request context",
)
def create_project_from_context_tool(
    name: str = "",
    tech_stack: list[str] | str | None = None,
    urls: list[str] | str | None = None,
    description: str = "",
    tags: list[str] | str | None = None,
    techStack: list[str] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any] | str:
    tool_name = "create_project"
    try:
        resolved_tech_stack = tech_stack if tech_stack is not None else techStack
        resolved_urls = urls if urls is not None else kwargs.get("url")
        resolved_tags = tags if tags is not None else kwargs.get("tag")
        resolved_description = description or str(kwargs.get("details", ""))
        oid = require_current_oid()
        project = create_project_for_user(
            oid=oid,
            name=name,
            tech_stack=_coerce_string_list(resolved_tech_stack),
            urls=_coerce_string_list(resolved_urls),
            description=resolved_description,
            tags=_coerce_string_list(resolved_tags),
        )
        return _tool_success(project)
    except Exception as exc:
        error = str(exc)
        return _tool_failure(tool_name, error)


@tool(
    name="query_projects",
    description="Get projects for the authenticated user from request context",
)
def query_projects_from_context_tool(
    tag: str = "",
    tags: str = "",
    tech: str = "",
    techs: str = "",
    name: str = "",
) -> dict[str, Any] | str:
    tool_name = "query_projects"
    try:
        oid = require_current_oid()
        projects = list_projects_for_user(
            oid=oid,
            tag=tag or None,
            tags=tags or None,
            tech=tech or None,
            techs=techs or None,
            name=name or None,
        )
        return _tool_success({"items": projects})
    except Exception as exc:
        error = str(exc)
        return _tool_failure(tool_name, error)
