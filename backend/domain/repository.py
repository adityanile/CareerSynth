from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, TypeVar

from sqlmodel import SQLModel, select

from db.models import (
    AchievementRecord,
    EducationRecord,
    ExperienceRecord,
    ProjectRecord,
    ResumeRecord,
)
from db.session import configure_database, get_session


class ProjectValidationError(Exception):
    pass


class ProjectNotFoundError(Exception):
    pass


class ProfileValidationError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


def configure_project_db(db_path: str) -> None:
    configure_database(use_sqlite=True, sqlite_db_path=db_path, database_url=None)


def configure_profile_db(db_path: str) -> None:
    configure_database(use_sqlite=True, sqlite_db_path=db_path, database_url=None)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_timestamp_text(value: datetime) -> str:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.astimezone(timezone.utc).isoformat()


def _parse_comma_separated(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalize_string_list(values: list[str], field_name: str) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ProjectValidationError(f"{field_name} must be a list of strings")
    normalized: list[str] = []
    for item in values:
        if item is None:
            continue
        value = item if isinstance(item, str) else str(item)
        value = value.strip()
        if value:
            normalized.append(value)
    return normalized


def _normalize_date(value: Optional[str], field_name: str, allow_null: bool = False) -> Optional[str]:
    if value is None and allow_null:
        return None
    if allow_null and isinstance(value, str) and not value.strip():
        return None
    if value is None:
        raise ProfileValidationError(f"{field_name} is required")

    normalized_value = value.strip()
    if not normalized_value:
        raise ProfileValidationError(f"{field_name} is required")
    return normalized_value


def _require_non_empty_text(value: Optional[str], field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ProfileValidationError(f"{field_name} cannot be empty")
    return normalized


def _row_to_project(row: ProjectRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "techStack": row.tech_stack or [],
        "urls": row.urls or [],
        "description": row.description,
        "tags": row.tags or [],
        "createdAt": _to_timestamp_text(row.created_at),
        "updatedAt": _to_timestamp_text(row.updated_at),
    }


def _row_to_experience(row: ExperienceRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "companyName": row.company_name,
        "startDate": row.start_date,
        "endDate": row.end_date,
        "position": row.position,
        "description": row.description,
        "location": row.location,
        "createdAt": _to_timestamp_text(row.created_at),
        "updatedAt": _to_timestamp_text(row.updated_at),
    }


def _row_to_achievement(row: AchievementRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "link": row.link,
        "organisation": row.organisation,
        "date": row.date,
        "createdAt": _to_timestamp_text(row.created_at),
        "updatedAt": _to_timestamp_text(row.updated_at),
    }


def _row_to_education(row: EducationRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "degreeName": row.degree_name,
        "location": row.location,
        "startYear": row.start_year,
        "endYear": row.end_year,
        "cgpaOrPercentage": row.cgpa_or_percentage,
        "createdAt": _to_timestamp_text(row.created_at),
        "updatedAt": _to_timestamp_text(row.updated_at),
    }


def _row_to_resume(row: ResumeRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "resumeName": row.resume_name,
        "resumeDescription": row.resume_description,
        "resume": row.resume,
        "createdOn": _to_timestamp_text(row.created_on),
        "updatedAt": _to_timestamp_text(row.updated_at),
    }


RecordType = TypeVar("RecordType", bound=SQLModel)


def _fetch_row_by_id_for_oid(
    *,
    model: type[RecordType],
    row_id: int,
    oid: str,
    not_found_message: str,
) -> RecordType:
    with get_session() as session:
        row = session.get(model, row_id)
        if row is None or getattr(row, "oid", None) != oid:
            raise ProfileNotFoundError(not_found_message)
        return row


def _delete_row_by_id_for_oid(
    *,
    model: type[RecordType],
    row_id: int,
    oid: str,
    not_found_message: str,
) -> None:
    with get_session() as session:
        row = session.get(model, row_id)
        if row is None or getattr(row, "oid", None) != oid:
            raise ProfileNotFoundError(not_found_message)
        session.delete(row)
        session.commit()


def list_projects_for_user(
    oid: str,
    tag: Optional[str] = None,
    tags: Optional[str] = None,
    tech: Optional[str] = None,
    techs: Optional[str] = None,
    name: Optional[str] = None,
) -> list[dict[str, Any]]:
    tag_values = []
    tech_values = []

    if tag:
        tag_values.append(tag.strip())
    tag_values.extend(_parse_comma_separated(tags))

    if tech:
        tech_values.append(tech.strip())
    tech_values.extend(_parse_comma_separated(techs))

    statement = select(ProjectRecord).where(ProjectRecord.oid == oid)
    if name and name.strip():
        statement = statement.where(ProjectRecord.name == name.strip())
    statement = statement.order_by(ProjectRecord.id.desc())

    with get_session() as session:
        rows = session.exec(statement).all()

    def _has_all(values: list[str], row_values: list[str]) -> bool:
        return all(value in row_values for value in values)

    filtered = [
        row
        for row in rows
        if _has_all(tag_values, row.tags or []) and _has_all(tech_values, row.tech_stack or [])
    ]

    return [_row_to_project(row) for row in filtered]


def create_project_for_user(
    oid: str,
    name: str,
    tech_stack: list[str],
    urls: list[str],
    description: str,
    tags: list[str],
) -> dict[str, Any]:
    normalized_name = name.strip()
    normalized_description = description.strip()

    if not normalized_name or not normalized_description:
        raise ProjectValidationError("name and description are required")

    row = ProjectRecord(
        oid=oid,
        name=normalized_name,
        tech_stack=_normalize_string_list(tech_stack, "techStack"),
        urls=_normalize_string_list(urls, "urls"),
        description=normalized_description,
        tags=_normalize_string_list(tags, "tags"),
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )

    with get_session() as session:
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_project(row)


def get_project_for_user(oid: str, project_id: int) -> dict[str, Any]:
    with get_session() as session:
        row = session.get(ProjectRecord, project_id)
    if row is None or row.oid != oid:
        raise ProjectNotFoundError("Project not found")
    return _row_to_project(row)


def get_projects_by_tag_for_user(oid: str, tag: str) -> list[dict[str, Any]]:
    tag_value = tag.strip()
    if not tag_value:
        raise ProjectValidationError("tag is required")

    with get_session() as session:
        rows = session.exec(
            select(ProjectRecord)
            .where(ProjectRecord.oid == oid)
            .order_by(ProjectRecord.id.desc())
        ).all()

    return [_row_to_project(row) for row in rows if tag_value in (row.tags or [])]


def update_project_for_user(oid: str, project_id: int, updates: dict[str, Any]) -> dict[str, Any]:
    if not updates:
        raise ProjectValidationError("No fields provided for update")

    with get_session() as session:
        row = session.get(ProjectRecord, project_id)
        if row is None or row.oid != oid:
            raise ProjectNotFoundError("Project not found")

        has_update = False

        if "name" in updates:
            value = (updates["name"] or "").strip()
            if not value:
                raise ProjectValidationError("name cannot be empty")
            row.name = value
            has_update = True

        if "description" in updates:
            value = (updates["description"] or "").strip()
            if not value:
                raise ProjectValidationError("description cannot be empty")
            row.description = value
            has_update = True

        if "techStack" in updates:
            row.tech_stack = _normalize_string_list(updates["techStack"], "techStack")
            has_update = True

        if "urls" in updates:
            row.urls = _normalize_string_list(updates["urls"], "urls")
            has_update = True

        if "tags" in updates:
            row.tags = _normalize_string_list(updates["tags"], "tags")
            has_update = True

        if not has_update:
            raise ProjectValidationError("No valid fields provided for update")

        row.updated_at = _utc_now()
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_project(row)


def delete_project_for_user(oid: str, project_id: int) -> None:
    with get_session() as session:
        row = session.get(ProjectRecord, project_id)
        if row is None or row.oid != oid:
            raise ProjectNotFoundError("Project not found")
        session.delete(row)
        session.commit()


def list_experiences_for_user(
    oid: str,
    position: Optional[str] = None,
    company_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    statement = select(ExperienceRecord).where(ExperienceRecord.oid == oid)

    if position and position.strip():
        statement = statement.where(ExperienceRecord.position == position.strip())
    if company_name and company_name.strip():
        statement = statement.where(ExperienceRecord.company_name == company_name.strip())

    statement = statement.order_by(ExperienceRecord.id.desc())

    with get_session() as session:
        rows = session.exec(statement).all()

    return [_row_to_experience(row) for row in rows]


def list_achievements_for_user(
    oid: str,
    organisation: Optional[str] = None,
    name: Optional[str] = None,
) -> list[dict[str, Any]]:
    statement = select(AchievementRecord).where(AchievementRecord.oid == oid)

    if organisation and organisation.strip():
        statement = statement.where(AchievementRecord.organisation == organisation.strip())
    if name and name.strip():
        statement = statement.where(AchievementRecord.name == name.strip())

    statement = statement.order_by(AchievementRecord.id.desc())

    with get_session() as session:
        rows = session.exec(statement).all()

    return [_row_to_achievement(row) for row in rows]


def list_educations_for_user(
    oid: str,
    degree_name: Optional[str] = None,
    location: Optional[str] = None,
) -> list[dict[str, Any]]:
    statement = select(EducationRecord).where(EducationRecord.oid == oid)

    if degree_name and degree_name.strip():
        statement = statement.where(EducationRecord.degree_name == degree_name.strip())
    if location and location.strip():
        statement = statement.where(EducationRecord.location == location.strip())

    statement = statement.order_by(EducationRecord.id.desc())

    with get_session() as session:
        rows = session.exec(statement).all()

    return [_row_to_education(row) for row in rows]


def list_resumes_for_user(
    oid: str,
    resume_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    statement = select(ResumeRecord).where(ResumeRecord.oid == oid)

    if resume_name and resume_name.strip():
        statement = statement.where(ResumeRecord.resume_name == resume_name.strip())

    statement = statement.order_by(ResumeRecord.id.desc())

    with get_session() as session:
        rows = session.exec(statement).all()

    return [_row_to_resume(row) for row in rows]


def create_experience_for_user(
    oid: str,
    company_name: str,
    start_date: str,
    end_date: Optional[str],
    position: str,
    description: str,
    location: str,
) -> dict[str, Any]:
    normalized_company_name = company_name.strip()
    normalized_position = position.strip()
    normalized_description = description.strip()
    normalized_location = location.strip()
    normalized_start_date = _normalize_date(start_date, "startDate")
    normalized_end_date = _normalize_date(end_date, "endDate", allow_null=True)

    if not normalized_company_name or not normalized_position or not normalized_description or not normalized_location:
        raise ProfileValidationError("companyName, position, description and location are required")

    row = ExperienceRecord(
        oid=oid,
        company_name=normalized_company_name,
        start_date=normalized_start_date,
        end_date=normalized_end_date,
        position=normalized_position,
        description=normalized_description,
        location=normalized_location,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )

    with get_session() as session:
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_experience(row)


def get_experience_for_user(oid: str, experience_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        model=ExperienceRecord,
        row_id=experience_id,
        oid=oid,
        not_found_message="Experience not found",
    )
    return _row_to_experience(row)


def update_experience_for_user(
    oid: str,
    experience_id: int,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise ProfileValidationError("No fields provided for update")

    with get_session() as session:
        row = session.get(ExperienceRecord, experience_id)
        if row is None or row.oid != oid:
            raise ProfileNotFoundError("Experience not found")

        has_update = False

        if "companyName" in updates:
            row.company_name = _require_non_empty_text(updates["companyName"], "companyName")
            has_update = True

        if "startDate" in updates:
            row.start_date = _normalize_date(updates["startDate"], "startDate")
            has_update = True

        if "endDate" in updates:
            row.end_date = _normalize_date(updates["endDate"], "endDate", allow_null=True)
            has_update = True

        if "position" in updates:
            row.position = _require_non_empty_text(updates["position"], "position")
            has_update = True

        if "description" in updates:
            row.description = _require_non_empty_text(updates["description"], "description")
            has_update = True

        if "location" in updates:
            row.location = _require_non_empty_text(updates["location"], "location")
            has_update = True

        if not has_update:
            raise ProfileValidationError("No valid fields provided for update")

        row.updated_at = _utc_now()
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_experience(row)


def delete_experience_for_user(oid: str, experience_id: int) -> None:
    _delete_row_by_id_for_oid(
        model=ExperienceRecord,
        row_id=experience_id,
        oid=oid,
        not_found_message="Experience not found",
    )


def create_achievement_for_user(
    oid: str,
    name: str,
    link: str,
    organisation: str,
    date: str,
) -> dict[str, Any]:
    normalized_name = name.strip()
    normalized_link = link.strip()
    normalized_organisation = organisation.strip()

    if not normalized_name or not normalized_link or not normalized_organisation:
        raise ProfileValidationError("name, link and organisation are required")

    row = AchievementRecord(
        oid=oid,
        name=normalized_name,
        link=normalized_link,
        organisation=normalized_organisation,
        date=_normalize_date(date, "date"),
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )

    with get_session() as session:
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_achievement(row)


def create_education_for_user(
    oid: str,
    degree_name: str,
    location: str,
    start_year: str,
    end_year: Optional[str],
    cgpa_or_percentage: str,
) -> dict[str, Any]:
    normalized_degree_name = degree_name.strip()
    normalized_location = location.strip()
    normalized_cgpa_or_percentage = cgpa_or_percentage.strip()
    normalized_start_year = _normalize_date(start_year, "startYear")
    normalized_end_year = _normalize_date(end_year, "endYear", allow_null=True)

    if not normalized_degree_name or not normalized_location or not normalized_cgpa_or_percentage:
        raise ProfileValidationError("degreeName, location and cgpaOrPercentage are required")

    row = EducationRecord(
        oid=oid,
        degree_name=normalized_degree_name,
        location=normalized_location,
        start_year=normalized_start_year,
        end_year=normalized_end_year,
        cgpa_or_percentage=normalized_cgpa_or_percentage,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )

    with get_session() as session:
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_education(row)


def create_resume_for_user(
    oid: str,
    resume_name: str,
    resume_description: str,
    resume: str,
) -> dict[str, Any]:
    normalized_resume_name = resume_name.strip()
    normalized_resume_description = resume_description.strip()
    normalized_resume = resume.strip()

    if not normalized_resume_name or not normalized_resume_description or not normalized_resume:
        raise ProfileValidationError("resumeName, resumeDescription and resume are required")

    row = ResumeRecord(
        oid=oid,
        user_reference=oid,
        resume_name=normalized_resume_name,
        resume_description=normalized_resume_description,
        resume=normalized_resume,
        created_on=_utc_now(),
        updated_at=_utc_now(),
    )

    with get_session() as session:
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_resume(row)


def get_achievement_for_user(oid: str, achievement_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        model=AchievementRecord,
        row_id=achievement_id,
        oid=oid,
        not_found_message="Achievement not found",
    )
    return _row_to_achievement(row)


def get_education_for_user(oid: str, education_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        model=EducationRecord,
        row_id=education_id,
        oid=oid,
        not_found_message="Education not found",
    )
    return _row_to_education(row)


def get_resume_for_user(oid: str, resume_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        model=ResumeRecord,
        row_id=resume_id,
        oid=oid,
        not_found_message="Resume not found",
    )
    return _row_to_resume(row)


def update_achievement_for_user(
    oid: str,
    achievement_id: int,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise ProfileValidationError("No fields provided for update")

    with get_session() as session:
        row = session.get(AchievementRecord, achievement_id)
        if row is None or row.oid != oid:
            raise ProfileNotFoundError("Achievement not found")

        has_update = False

        if "name" in updates:
            row.name = _require_non_empty_text(updates["name"], "name")
            has_update = True

        if "link" in updates:
            row.link = _require_non_empty_text(updates["link"], "link")
            has_update = True

        if "organisation" in updates:
            row.organisation = _require_non_empty_text(updates["organisation"], "organisation")
            has_update = True

        if "date" in updates:
            row.date = _normalize_date(updates["date"], "date")
            has_update = True

        if not has_update:
            raise ProfileValidationError("No valid fields provided for update")

        row.updated_at = _utc_now()
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_achievement(row)


def update_education_for_user(
    oid: str,
    education_id: int,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise ProfileValidationError("No fields provided for update")

    with get_session() as session:
        row = session.get(EducationRecord, education_id)
        if row is None or row.oid != oid:
            raise ProfileNotFoundError("Education not found")

        has_update = False

        if "degreeName" in updates:
            row.degree_name = _require_non_empty_text(updates["degreeName"], "degreeName")
            has_update = True

        if "location" in updates:
            row.location = _require_non_empty_text(updates["location"], "location")
            has_update = True

        if "startYear" in updates:
            row.start_year = _normalize_date(updates["startYear"], "startYear")
            has_update = True

        if "endYear" in updates:
            row.end_year = _normalize_date(updates["endYear"], "endYear", allow_null=True)
            has_update = True

        if "cgpaOrPercentage" in updates:
            row.cgpa_or_percentage = _require_non_empty_text(updates["cgpaOrPercentage"], "cgpaOrPercentage")
            has_update = True

        if not has_update:
            raise ProfileValidationError("No valid fields provided for update")

        row.updated_at = _utc_now()
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_education(row)


def update_resume_for_user(
    oid: str,
    resume_id: int,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise ProfileValidationError("No fields provided for update")

    with get_session() as session:
        row = session.get(ResumeRecord, resume_id)
        if row is None or row.oid != oid:
            raise ProfileNotFoundError("Resume not found")

        has_update = False

        if "resumeName" in updates:
            row.resume_name = _require_non_empty_text(updates["resumeName"], "resumeName")
            has_update = True

        if "resumeDescription" in updates:
            row.resume_description = _require_non_empty_text(updates["resumeDescription"], "resumeDescription")
            has_update = True

        if "resume" in updates:
            row.resume = _require_non_empty_text(updates["resume"], "resume")
            has_update = True

        if not has_update:
            raise ProfileValidationError("No valid fields provided for update")

        row.updated_at = _utc_now()
        session.add(row)
        session.commit()
        session.refresh(row)

    return _row_to_resume(row)


def delete_achievement_for_user(oid: str, achievement_id: int) -> None:
    _delete_row_by_id_for_oid(
        model=AchievementRecord,
        row_id=achievement_id,
        oid=oid,
        not_found_message="Achievement not found",
    )


def delete_education_for_user(oid: str, education_id: int) -> None:
    _delete_row_by_id_for_oid(
        model=EducationRecord,
        row_id=education_id,
        oid=oid,
        not_found_message="Education not found",
    )


def delete_resume_for_user(oid: str, resume_id: int) -> None:
    _delete_row_by_id_for_oid(
        model=ResumeRecord,
        row_id=resume_id,
        oid=oid,
        not_found_message="Resume not found",
    )
