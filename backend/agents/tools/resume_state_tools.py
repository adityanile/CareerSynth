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
    return {
        "projects": list(projects) if isinstance(projects, list) else [],
        "experiences": list(experiences) if isinstance(experiences, list) else [],
        "achievements": list(achievements) if isinstance(achievements, list) else [],
    }


def _append_to_state_list(cache_key: CacheKey, key: str, item: dict[str, Any]) -> list[dict[str, Any]]:
    lock = _get_lock_for_cache_key(cache_key)
    with lock:
        state_payload = _get_cached_resume_state(cache_key)
        updated_list = [*state_payload[key], item]
        state_payload[key] = updated_list
        resume_state_cache[cache_key] = state_payload
        return updated_list


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
