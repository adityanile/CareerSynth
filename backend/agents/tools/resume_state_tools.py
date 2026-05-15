from __future__ import annotations

from threading import Lock
from typing import Any

from agent_framework import tool
from agent_framework.ag_ui import state_update

from agents.context import require_current_oid, require_current_thread_id

CacheKey = tuple[str, str]

resume_state_cache: dict[CacheKey, dict[str, Any]] = {}
resume_state_locks: dict[CacheKey, Lock] = {}
resume_state_locks_guard = Lock()


def _empty_resume_state_payload() -> dict[str, Any]:
    return {
        "projects": [],
        "experiences": [],
        "achievements": [],
        "educations": [],
        "summary": "",
        "skills": [],
        "profile": {
            "name": "",
            "role": "",
            "contact": "",
            "location": "",
            "linkedinUrl": "",
            "additionalUrls": [],
        },
    }


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


def _cache_key(oid: str, thread_id: str) -> CacheKey:
    return (oid, thread_id)


def _get_lock_for_cache_key(key: CacheKey) -> Lock:
    with resume_state_locks_guard:
        lock = resume_state_locks.get(key)
        if lock is None:
            lock = Lock()
            resume_state_locks[key] = lock
        return lock


def _get_cached_resume_state(key: CacheKey) -> dict[str, Any]:
    cached_state = resume_state_cache.get(key, _empty_resume_state_payload())
    projects = cached_state.get("projects")
    experiences = cached_state.get("experiences")
    achievements = cached_state.get("achievements")
    educations = cached_state.get("educations")
    summary = cached_state.get("summary")
    skills = cached_state.get("skills")
    profile = cached_state.get("profile")
    profile_payload = profile if isinstance(profile, dict) else {}
    return {
        "projects": list(projects) if isinstance(projects, list) else [],
        "experiences": list(experiences) if isinstance(experiences, list) else [],
        "achievements": list(achievements) if isinstance(achievements, list) else [],
        "educations": list(educations) if isinstance(educations, list) else [],
        "summary": str(summary).strip() if isinstance(summary, str) else "",
        "skills": _normalize_string_list(skills),
        "profile": {
            "name": str(profile_payload.get("name") or "").strip(),
            "role": str(profile_payload.get("role") or "").strip(),
            "contact": str(profile_payload.get("contact") or "").strip(),
            "location": str(profile_payload.get("location") or "").strip(),
            "linkedinUrl": str(profile_payload.get("linkedinUrl") or "").strip(),
            "additionalUrls": _normalize_string_list(profile_payload.get("additionalUrls")),
        },
    }


def _append_to_state_list(cache_key: CacheKey, key: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    lock = _get_lock_for_cache_key(cache_key)
    with lock:
        state_payload = _get_cached_resume_state(cache_key)
        updated_list = [*state_payload[key], item]
        state_payload[key] = updated_list
        resume_state_cache[cache_key] = state_payload
        return updated_list


def _set_state_string(cache_key: CacheKey, key: str, value: str) -> str:
    lock = _get_lock_for_cache_key(cache_key)
    with lock:
        state_payload = _get_cached_resume_state(cache_key)
        state_payload[key] = value
        resume_state_cache[cache_key] = state_payload
        return value


def _set_state_object(cache_key: CacheKey, key: str, value: dict[str, Any]) -> dict[str, Any]:
    lock = _get_lock_for_cache_key(cache_key)
    with lock:
        state_payload = _get_cached_resume_state(cache_key)
        state_payload[key] = value
        resume_state_cache[cache_key] = state_payload
        return value


def _set_state_list(cache_key: CacheKey, key: str, value: list[str]) -> list[str]:
    lock = _get_lock_for_cache_key(cache_key)
    with lock:
        state_payload = _get_cached_resume_state(cache_key)
        state_payload[key] = value
        resume_state_cache[cache_key] = state_payload
        return value


@tool(
    name="add_project_to_resume",
    description=(
        "Append a project to shared resume state using a project object with "
        "projectName, description, and techStack."
    ),
)
def add_project_to_resume_tool(project: dict[str, Any] | None = None) -> Any:
    if not isinstance(project, dict):
        raise ValueError("project object is required")

    project_record = {
        "name": _normalize_required_string(
            project.get("projectName") or project.get("projectname"),
            "projectName",
        ),
        "description": _normalize_required_string(project.get("description"), "description"),
        "techStack": _normalize_string_list(project.get("techStack")),
    }

    oid = require_current_oid()
    thread_id = require_current_thread_id()
    updated_projects = _append_to_state_list(_cache_key(oid, thread_id), "projects", project_record)
    return state_update(
        text=f"Added project '{project_record['name']}' to shared resume state list.",
        state={"projects": updated_projects},
    )


@tool(
    name="add_experience_to_resume",
    description=(
        "Append an experience to shared resume state using an experience object "
        "with companyName, position, description, startDate, optional endDate, and location."
    ),
)
def add_experience_to_resume_tool(experience: dict[str, Any] | None = None) -> Any:
    if not isinstance(experience, dict):
        raise ValueError("experience object is required")

    experience_record = {
        "companyName": _normalize_required_string(experience.get("companyName"), "companyName"),
        "position": _normalize_required_string(experience.get("position"), "position"),
        "description": _normalize_required_string(experience.get("description"), "description"),
        "startDate": _normalize_required_string(experience.get("startDate"), "startDate"),
        "endDate": _normalize_optional_string(experience.get("endDate")),
        "location": _normalize_required_string(experience.get("location"), "location"),
    }

    oid = require_current_oid()
    thread_id = require_current_thread_id()
    updated_experiences = _append_to_state_list(
        _cache_key(oid, thread_id),
        "experiences",
        experience_record,
    )
    return state_update(
        text=(
            f"Added experience '{experience_record['position']} @ "
            f"{experience_record['companyName']}' to shared resume state list."
        ),
        state={"experiences": updated_experiences},
    )


@tool(
    name="add_achievement_to_resume",
    description=(
        "Append an achievement to shared resume state using an achievement object "
        "with name, organisation, date, and link."
    ),
)
def add_achievement_to_resume_tool(achievement: dict[str, Any] | None = None) -> Any:
    if not isinstance(achievement, dict):
        raise ValueError("achievement object is required")

    achievement_record = {
        "name": _normalize_required_string(achievement.get("name"), "name"),
        "organisation": _normalize_required_string(
            achievement.get("organisation"),
            "organisation",
        ),
        "date": _normalize_required_string(achievement.get("date"), "date"),
        "link": _normalize_required_string(achievement.get("link"), "link"),
    }

    oid = require_current_oid()
    thread_id = require_current_thread_id()
    updated_achievements = _append_to_state_list(
        _cache_key(oid, thread_id),
        "achievements",
        achievement_record,
    )
    return state_update(
        text=f"Added achievement '{achievement_record['name']}' to shared resume state list.",
        state={"achievements": updated_achievements},
    )


@tool(
    name="add_education_to_resume",
    description=(
        "Append an education item to shared resume state using an education object "
        "with degreeName, location, startYear, optional endYear, and cgpaOrPercentage."
    ),
)
def add_education_to_resume_tool(education: dict[str, Any] | None = None) -> Any:
    if not isinstance(education, dict):
        raise ValueError("education object is required")

    education_record = {
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

    oid = require_current_oid()
    thread_id = require_current_thread_id()
    updated_educations = _append_to_state_list(
        _cache_key(oid, thread_id),
        "educations",
        education_record,
    )
    return state_update(
        text=f"Added education '{education_record['degreeName']}' to shared resume state list.",
        state={"educations": updated_educations},
    )


@tool(
    name="add_summary",
    description="Set shared resume summary using a non-empty string value.",
)
def add_summary_tool(summary: str | None = None) -> Any:
    summary_value = _normalize_required_string(summary, "summary")

    oid = require_current_oid()
    thread_id = require_current_thread_id()
    updated_summary = _set_state_string(
        _cache_key(oid, thread_id),
        "summary",
        summary_value,
    )
    return state_update(
        text="Updated summary in shared resume state.",
        state={"summary": updated_summary},
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

    oid = require_current_oid()
    thread_id = require_current_thread_id()
    updated_profile = _set_state_object(
        _cache_key(oid, thread_id),
        "profile",
        profile_record,
    )
    return state_update(
        text=f"Updated profile in shared resume state for '{profile_record['name']}'.",
        state={"profile": updated_profile},
    )


@tool(
    name="add_skills",
    description="Set shared resume skills using a non-empty list of strings.",
)
def add_skills_tool(skills: list[str] | str | None = None) -> Any:
    skills_list = _normalize_string_list(skills)
    if not skills_list:
        raise ValueError("skills are required")

    oid = require_current_oid()
    thread_id = require_current_thread_id()
    updated_skills = _set_state_list(
        _cache_key(oid, thread_id),
        "skills",
        skills_list,
    )
    return state_update(
        text=f"Updated {len(updated_skills)} skills in shared resume state.",
        state={"skills": updated_skills},
    )
