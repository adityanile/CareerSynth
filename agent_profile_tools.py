from typing import Any

from agent_framework import tool

from agent_request_context import require_current_oid
from profile_tools import create_achievement_for_user, create_experience_for_user
from tool_response import format_tool_failure


def _tool_success(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _tool_failure(tool_name: str, error: str) -> str:
    return format_tool_failure(tool_name=tool_name, error=error)


@tool(
    name="create_experience",
    description="Create an experience for the authenticated user from request context",
)
def create_experience_from_context_tool(
    company_name: str = "",
    start_date: str = "",
    end_date: str = "",
    position: str = "",
    description: str = "",
    location: str = "",
    companyName: str = "",
    startDate: str = "",
    endDate: str = "",
    role: str = "",
    jobDescription: str = "",
    workLocation: str = "",
    details: str = "",
    city: str = "",
) -> dict[str, Any] | str:
    tool_name = "create_experience"
    try:
        resolved_company_name = company_name or companyName
        resolved_start_date = start_date or startDate
        resolved_end_date = end_date or endDate or None
        resolved_position = position or role
        resolved_description = description or jobDescription or details
        resolved_location = location or workLocation or city
        oid = require_current_oid()
        experience = create_experience_for_user(
            oid=oid,
            company_name=resolved_company_name,
            start_date=resolved_start_date,
            end_date=resolved_end_date,
            position=resolved_position,
            description=resolved_description,
            location=resolved_location,
        )
        return _tool_success(experience)
    except Exception as exc:
        error = str(exc)
        return _tool_failure(tool_name, error)


@tool(
    name="create_achievement",
    description="Create an achievement for the authenticated user from request context",
)
def create_achievement_from_context_tool(
    name: str = "",
    link: str = "",
    organisation: str = "",
    date: str = "",
    organization: str = "",
    url: str = "",
) -> dict[str, Any] | str:
    tool_name = "create_achievement"
    try:
        resolved_organisation = organisation or organization
        resolved_link = link or url
        oid = require_current_oid()
        achievement = create_achievement_for_user(
            oid=oid,
            name=name,
            link=resolved_link,
            organisation=resolved_organisation,
            date=date,
        )
        return _tool_success(achievement)
    except Exception as exc:
        error = str(exc)
        return _tool_failure(tool_name, error)
