from __future__ import annotations

from typing import Any

from agent_framework import tool
from agent_framework.ag_ui import state_update


def _normalize_required_string(value: Any, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalize_optional_string(value: Any) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _normalize_project_record(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _normalize_required_string(
            project.get("projectName") or project.get("projectname"),
            "projectName",
        ),
        "description": _normalize_required_string(project.get("description"), "description"),
        "techStack": _normalize_string_list(project.get("techStack")),
    }


def _normalize_experience_record(experience: dict[str, Any]) -> dict[str, Any]:
    return {
        "companyName": _normalize_required_string(experience.get("companyName"), "companyName"),
        "position": _normalize_required_string(experience.get("position"), "position"),
        "description": _normalize_required_string(experience.get("description"), "description"),
        "startDate": _normalize_required_string(experience.get("startDate"), "startDate"),
        "endDate": _normalize_optional_string(experience.get("endDate")),
        "location": _normalize_required_string(experience.get("location"), "location"),
    }


def _normalize_achievement_record(achievement: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _normalize_required_string(achievement.get("name"), "name"),
        "organisation": _normalize_required_string(
            achievement.get("organisation"),
            "organisation",
        ),
        "date": _normalize_required_string(achievement.get("date"), "date"),
        "link": _normalize_required_string(achievement.get("link"), "link"),
    }


def _normalize_education_record(education: dict[str, Any]) -> dict[str, Any]:
    return {
        "degreeName": _normalize_required_string(
            education.get("degreeName") or education.get("degreename"),
            "degreeName",
        ),
        "location": _normalize_required_string(education.get("location"), "location"),
        "startYear": _normalize_required_string(
            education.get("startYear") or education.get("startyear"),
            "startYear",
        ),
        "endYear": _normalize_optional_string(education.get("endYear") or education.get("endyear")),
        "cgpaOrPercentage": _normalize_required_string(
            education.get("cgpaOrPercentage") or education.get("cgpa/percentage"),
            "cgpaOrPercentage",
        ),
    }


def _normalize_record_list(
    records: list[dict[str, Any]] | None,
    single_record: dict[str, Any] | None,
    list_field_name: str,
    single_field_name: str,
    normalizer: Any,
) -> list[dict[str, Any]]:
    if isinstance(records, list):
        normalized: list[dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(f"{single_field_name} object is required")
            normalized.append(normalizer(record))
        if not normalized:
            raise ValueError(f"{list_field_name} are required")
        return normalized

    if isinstance(single_record, dict):
        return [normalizer(single_record)]

    raise ValueError(f"{list_field_name} are required")


@tool(
    name="add_project_to_resume",
    description=(
        "Set shared resume projects using `projects` list of project objects with "
        "projectName, description, and techStack."
    ),
)
def add_project_to_resume_tool(
    projects: list[dict[str, Any]] | None = None,
    project: dict[str, Any] | None = None,
) -> Any:
    project_records = _normalize_record_list(
        projects,
        project,
        "projects",
        "project",
        _normalize_project_record,
    )
    return state_update(
        text=f"Updated {len(project_records)} projects in shared resume state.",
        state={"projects": project_records},
    )


@tool(
    name="add_experience_to_resume",
    description=(
        "Set shared resume experiences using `experiences` list of experience objects "
        "with companyName, position, description, startDate, optional endDate, and location."
    ),
)
def add_experience_to_resume_tool(
    experiences: list[dict[str, Any]] | None = None,
    experience: dict[str, Any] | None = None,
) -> Any:
    experience_records = _normalize_record_list(
        experiences,
        experience,
        "experiences",
        "experience",
        _normalize_experience_record,
    )
    return state_update(
        text=f"Updated {len(experience_records)} experiences in shared resume state.",
        state={"experiences": experience_records},
    )


@tool(
    name="add_achievement_to_resume",
    description=(
        "Set shared resume achievements using `achievements` list of achievement objects "
        "with name, organisation, date, and link."
    ),
)
def add_achievement_to_resume_tool(
    achievements: list[dict[str, Any]] | None = None,
    achievement: dict[str, Any] | None = None,
) -> Any:
    achievement_records = _normalize_record_list(
        achievements,
        achievement,
        "achievements",
        "achievement",
        _normalize_achievement_record,
    )
    return state_update(
        text=f"Updated {len(achievement_records)} achievements in shared resume state.",
        state={"achievements": achievement_records},
    )


@tool(
    name="add_education_to_resume",
    description=(
        "Set shared resume educations using `educations` list of education objects "
        "with degreeName, location, startYear, optional endYear, and cgpaOrPercentage."
    ),
)
def add_education_to_resume_tool(
    educations: list[dict[str, Any]] | None = None,
    education: dict[str, Any] | None = None,
) -> Any:
    education_records = _normalize_record_list(
        educations,
        education,
        "educations",
        "education",
        _normalize_education_record,
    )
    return state_update(
        text=f"Updated {len(education_records)} educations in shared resume state.",
        state={"educations": education_records},
    )


@tool(
    name="add_summary",
    description="Set shared resume summary using a non-empty string value.",
)
def add_summary_tool(summary: str | None = None) -> Any:
    summary_value = _normalize_required_string(summary, "summary")
    return state_update(
        text="Updated summary in shared resume state.",
        state={"summary": summary_value},
    )


@tool(
    name="add_profile",
    description=(
        "Set shared resume profile using a profile object with "
        "name, role, contact, location, linkedinUrl, and additionalUrls."
    ),
)
def add_profile_tool(profile: dict[str, Any] | None = None) -> Any:
    if not isinstance(profile, dict):
        raise ValueError("profile object is required")

    profile_record = {
        "name": _normalize_required_string(profile.get("name"), "name"),
        "role": _normalize_required_string(profile.get("role"), "role"),
        "contact": _normalize_required_string(profile.get("contact"), "contact"),
        "location": _normalize_required_string(profile.get("location"), "location"),
        "linkedinUrl": _normalize_required_string(
            profile.get("linkedinUrl") or profile.get("linkedinurl"),
            "linkedinUrl",
        ),
        "additionalUrls": _normalize_string_list(
            profile.get("additionalUrls") or profile.get("additionalurls"),
        ),
    }

    return state_update(
        text=f"Updated profile in shared resume state for '{profile_record['name']}'.",
        state={"profile": profile_record},
    )


@tool(
    name="add_skills",
    description="Set shared resume skills using a non-empty list of strings.",
)
def add_skills_tool(skills: list[str] | str | None = None) -> Any:
    skills_list = _normalize_string_list(skills)
    if not skills_list:
        raise ValueError("skills are required")

    return state_update(
        text=f"Updated {len(skills_list)} skills in shared resume state.",
        state={"skills": skills_list},
    )
