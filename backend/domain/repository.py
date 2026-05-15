import json
import sqlite3
from typing import Any, Optional


class ProjectValidationError(Exception):
    pass


class ProjectNotFoundError(Exception):
    pass


class ProfileValidationError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


_db_path = "careersynth.db"


def configure_project_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path


def configure_profile_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn


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


def _row_to_project(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "techStack": json.loads(row["tech_stack"]),
        "urls": json.loads(row["urls"]),
        "description": row["description"],
        "tags": json.loads(row["tags"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_experience(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "companyName": row["company_name"],
        "startDate": row["start_date"],
        "endDate": row["end_date"],
        "position": row["position"],
        "description": row["description"],
        "location": row["location"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_achievement(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "link": row["link"],
        "organisation": row["organisation"],
        "date": row["date"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_education(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "degreeName": row["degree_name"],
        "location": row["location"],
        "startYear": row["start_year"],
        "endYear": row["end_year"],
        "cgpaOrPercentage": row["cgpa_or_percentage"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_resume(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "resumeName": row["resume_name"],
        "resumeDescription": row["resume_description"],
        "resume": row["resume"],
        "createdOn": row["created_on"],
        "updatedAt": row["updated_at"],
    }


def _list_rows_for_oid(
    *,
    table: str,
    oid: str,
    filters: dict[str, Optional[str]] | None = None,
) -> list[sqlite3.Row]:
    where_clauses = ["oid = ?"]
    params: list[Any] = [oid]

    for column, value in (filters or {}).items():
        if value is None:
            continue
        normalized = value.strip()
        if not normalized:
            continue
        where_clauses.append(f"{column} = ?")
        params.append(normalized)

    sql = f"SELECT * FROM {table} WHERE {' AND '.join(where_clauses)} ORDER BY id DESC"
    with _get_db_connection() as conn:
        return conn.execute(sql, params).fetchall()


def _fetch_row_by_id_for_oid(*, table: str, row_id: int, oid: str, not_found_message: str) -> sqlite3.Row:
    with _get_db_connection() as conn:
        row = conn.execute(
            f"SELECT * FROM {table} WHERE id = ? AND oid = ?",
            (row_id, oid),
        ).fetchone()
    if not row:
        raise ProfileNotFoundError(not_found_message)
    return row


def _delete_row_by_id_for_oid(*, table: str, row_id: int, oid: str, not_found_message: str) -> None:
    with _get_db_connection() as conn:
        cursor = conn.execute(
            f"DELETE FROM {table} WHERE id = ? AND oid = ?",
            (row_id, oid),
        )
    if cursor.rowcount == 0:
        raise ProfileNotFoundError(not_found_message)


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

    where_clauses = ["oid = ?"]
    params: list[Any] = [oid]

    if name and name.strip():
        where_clauses.append("name = ?")
        params.append(name.strip())

    for value in tag_values:
        where_clauses.append("EXISTS (SELECT 1 FROM json_each(projects.tags) WHERE json_each.value = ?)")
        params.append(value)

    for value in tech_values:
        where_clauses.append("EXISTS (SELECT 1 FROM json_each(projects.tech_stack) WHERE json_each.value = ?)")
        params.append(value)

    sql = f"SELECT * FROM projects WHERE {' AND '.join(where_clauses)} ORDER BY id DESC"
    with _get_db_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_project(row) for row in rows]


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

    normalized_tech_stack = _normalize_string_list(tech_stack, "techStack")
    normalized_urls = _normalize_string_list(urls, "urls")
    normalized_tags = _normalize_string_list(tags, "tags")

    with _get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO projects (oid, name, tech_stack, urls, description, tags)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                oid,
                normalized_name,
                json.dumps(normalized_tech_stack),
                json.dumps(normalized_urls),
                normalized_description,
                json.dumps(normalized_tags),
            ),
        )
        project_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ? AND oid = ?",
            (project_id, oid),
        ).fetchone()

    return _row_to_project(row)


def get_project_for_user(oid: str, project_id: int) -> dict[str, Any]:
    with _get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ? AND oid = ?",
            (project_id, oid),
        ).fetchone()

    if not row:
        raise ProjectNotFoundError("Project not found")
    return _row_to_project(row)


def get_projects_by_tag_for_user(oid: str, tag: str) -> list[dict[str, Any]]:
    tag_value = tag.strip()
    if not tag_value:
        raise ProjectValidationError("tag is required")

    with _get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM projects
            WHERE oid = ?
              AND EXISTS (SELECT 1 FROM json_each(projects.tags) WHERE json_each.value = ?)
            ORDER BY id DESC
            """,
            (oid, tag_value),
        ).fetchall()

    return [_row_to_project(row) for row in rows]


def update_project_for_user(oid: str, project_id: int, updates: dict[str, Any]) -> dict[str, Any]:
    if not updates:
        raise ProjectValidationError("No fields provided for update")

    set_clauses: list[str] = []
    params: list[Any] = []

    if "name" in updates:
        value = (updates["name"] or "").strip()
        if not value:
            raise ProjectValidationError("name cannot be empty")
        set_clauses.append("name = ?")
        params.append(value)

    if "description" in updates:
        value = (updates["description"] or "").strip()
        if not value:
            raise ProjectValidationError("description cannot be empty")
        set_clauses.append("description = ?")
        params.append(value)

    if "techStack" in updates:
        normalized = _normalize_string_list(updates["techStack"], "techStack")
        set_clauses.append("tech_stack = ?")
        params.append(json.dumps(normalized))

    if "urls" in updates:
        normalized = _normalize_string_list(updates["urls"], "urls")
        set_clauses.append("urls = ?")
        params.append(json.dumps(normalized))

    if "tags" in updates:
        normalized = _normalize_string_list(updates["tags"], "tags")
        set_clauses.append("tags = ?")
        params.append(json.dumps(normalized))

    if not set_clauses:
        raise ProjectValidationError("No valid fields provided for update")

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([project_id, oid])

    with _get_db_connection() as conn:
        cursor = conn.execute(
            f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ? AND oid = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise ProjectNotFoundError("Project not found")
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ? AND oid = ?",
            (project_id, oid),
        ).fetchone()

    return _row_to_project(row)


def delete_project_for_user(oid: str, project_id: int) -> None:
    with _get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM projects WHERE id = ? AND oid = ?",
            (project_id, oid),
        )

    if cursor.rowcount == 0:
        raise ProjectNotFoundError("Project not found")


def list_experiences_for_user(
    oid: str,
    position: Optional[str] = None,
    company_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    rows = _list_rows_for_oid(
        table="experiences",
        oid=oid,
        filters={"position": position, "company_name": company_name},
    )
    return [_row_to_experience(row) for row in rows]


def list_achievements_for_user(
    oid: str,
    organisation: Optional[str] = None,
    name: Optional[str] = None,
) -> list[dict[str, Any]]:
    rows = _list_rows_for_oid(
        table="achievements",
        oid=oid,
        filters={"organisation": organisation, "name": name},
    )
    return [_row_to_achievement(row) for row in rows]


def list_educations_for_user(
    oid: str,
    degree_name: Optional[str] = None,
    location: Optional[str] = None,
) -> list[dict[str, Any]]:
    rows = _list_rows_for_oid(
        table="educations",
        oid=oid,
        filters={"degree_name": degree_name, "location": location},
    )
    return [_row_to_education(row) for row in rows]


def list_resumes_for_user(
    oid: str,
    resume_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    rows = _list_rows_for_oid(
        table="resumes",
        oid=oid,
        filters={"resume_name": resume_name},
    )
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

    with _get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO experiences (oid, company_name, start_date, end_date, position, description, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                oid,
                normalized_company_name,
                normalized_start_date,
                normalized_end_date,
                normalized_position,
                normalized_description,
                normalized_location,
            ),
        )
        experience_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM experiences WHERE id = ? AND oid = ?",
            (experience_id, oid),
        ).fetchone()

    return _row_to_experience(row)


def get_experience_for_user(oid: str, experience_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        table="experiences",
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

    set_clauses: list[str] = []
    params: list[Any] = []

    if "companyName" in updates:
        set_clauses.append("company_name = ?")
        params.append(_require_non_empty_text(updates["companyName"], "companyName"))

    if "startDate" in updates:
        set_clauses.append("start_date = ?")
        params.append(_normalize_date(updates["startDate"], "startDate"))

    if "endDate" in updates:
        set_clauses.append("end_date = ?")
        params.append(_normalize_date(updates["endDate"], "endDate", allow_null=True))

    if "position" in updates:
        set_clauses.append("position = ?")
        params.append(_require_non_empty_text(updates["position"], "position"))

    if "description" in updates:
        set_clauses.append("description = ?")
        params.append(_require_non_empty_text(updates["description"], "description"))

    if "location" in updates:
        set_clauses.append("location = ?")
        params.append(_require_non_empty_text(updates["location"], "location"))

    if not set_clauses:
        raise ProfileValidationError("No valid fields provided for update")

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([experience_id, oid])

    with _get_db_connection() as conn:
        cursor = conn.execute(
            f"UPDATE experiences SET {', '.join(set_clauses)} WHERE id = ? AND oid = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise ProfileNotFoundError("Experience not found")
        row = conn.execute(
            "SELECT * FROM experiences WHERE id = ? AND oid = ?",
            (experience_id, oid),
        ).fetchone()
    return _row_to_experience(row)


def delete_experience_for_user(oid: str, experience_id: int) -> None:
    _delete_row_by_id_for_oid(
        table="experiences",
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

    normalized_date = _normalize_date(date, "date")

    with _get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO achievements (oid, name, link, organisation, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (oid, normalized_name, normalized_link, normalized_organisation, normalized_date),
        )
        achievement_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM achievements WHERE id = ? AND oid = ?",
            (achievement_id, oid),
        ).fetchone()

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

    with _get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO educations (oid, degree_name, location, start_year, end_year, cgpa_or_percentage)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                oid,
                normalized_degree_name,
                normalized_location,
                normalized_start_year,
                normalized_end_year,
                normalized_cgpa_or_percentage,
            ),
        )
        education_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM educations WHERE id = ? AND oid = ?",
            (education_id, oid),
        ).fetchone()

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

    with _get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO resumes (oid, user_reference, resume_name, resume_description, resume)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                oid,
                oid,
                normalized_resume_name,
                normalized_resume_description,
                normalized_resume,
            ),
        )
        resume_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM resumes WHERE id = ? AND oid = ?",
            (resume_id, oid),
        ).fetchone()

    return _row_to_resume(row)


def get_achievement_for_user(oid: str, achievement_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        table="achievements",
        row_id=achievement_id,
        oid=oid,
        not_found_message="Achievement not found",
    )
    return _row_to_achievement(row)


def get_education_for_user(oid: str, education_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        table="educations",
        row_id=education_id,
        oid=oid,
        not_found_message="Education not found",
    )
    return _row_to_education(row)


def get_resume_for_user(oid: str, resume_id: int) -> dict[str, Any]:
    row = _fetch_row_by_id_for_oid(
        table="resumes",
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

    set_clauses: list[str] = []
    params: list[Any] = []

    if "name" in updates:
        set_clauses.append("name = ?")
        params.append(_require_non_empty_text(updates["name"], "name"))

    if "link" in updates:
        set_clauses.append("link = ?")
        params.append(_require_non_empty_text(updates["link"], "link"))

    if "organisation" in updates:
        set_clauses.append("organisation = ?")
        params.append(_require_non_empty_text(updates["organisation"], "organisation"))

    if "date" in updates:
        set_clauses.append("date = ?")
        params.append(_normalize_date(updates["date"], "date"))

    if not set_clauses:
        raise ProfileValidationError("No valid fields provided for update")

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([achievement_id, oid])

    with _get_db_connection() as conn:
        cursor = conn.execute(
            f"UPDATE achievements SET {', '.join(set_clauses)} WHERE id = ? AND oid = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise ProfileNotFoundError("Achievement not found")
        row = conn.execute(
            "SELECT * FROM achievements WHERE id = ? AND oid = ?",
            (achievement_id, oid),
        ).fetchone()
    return _row_to_achievement(row)


def update_education_for_user(
    oid: str,
    education_id: int,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise ProfileValidationError("No fields provided for update")

    set_clauses: list[str] = []
    params: list[Any] = []

    if "degreeName" in updates:
        set_clauses.append("degree_name = ?")
        params.append(_require_non_empty_text(updates["degreeName"], "degreeName"))

    if "location" in updates:
        set_clauses.append("location = ?")
        params.append(_require_non_empty_text(updates["location"], "location"))

    if "startYear" in updates:
        set_clauses.append("start_year = ?")
        params.append(_normalize_date(updates["startYear"], "startYear"))

    if "endYear" in updates:
        set_clauses.append("end_year = ?")
        params.append(_normalize_date(updates["endYear"], "endYear", allow_null=True))

    if "cgpaOrPercentage" in updates:
        set_clauses.append("cgpa_or_percentage = ?")
        params.append(_require_non_empty_text(updates["cgpaOrPercentage"], "cgpaOrPercentage"))

    if not set_clauses:
        raise ProfileValidationError("No valid fields provided for update")

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([education_id, oid])

    with _get_db_connection() as conn:
        cursor = conn.execute(
            f"UPDATE educations SET {', '.join(set_clauses)} WHERE id = ? AND oid = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise ProfileNotFoundError("Education not found")
        row = conn.execute(
            "SELECT * FROM educations WHERE id = ? AND oid = ?",
            (education_id, oid),
        ).fetchone()
    return _row_to_education(row)


def update_resume_for_user(
    oid: str,
    resume_id: int,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise ProfileValidationError("No fields provided for update")

    set_clauses: list[str] = []
    params: list[Any] = []

    if "resumeName" in updates:
        set_clauses.append("resume_name = ?")
        params.append(_require_non_empty_text(updates["resumeName"], "resumeName"))

    if "resumeDescription" in updates:
        set_clauses.append("resume_description = ?")
        params.append(_require_non_empty_text(updates["resumeDescription"], "resumeDescription"))

    if "resume" in updates:
        set_clauses.append("resume = ?")
        params.append(_require_non_empty_text(updates["resume"], "resume"))

    if not set_clauses:
        raise ProfileValidationError("No valid fields provided for update")

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([resume_id, oid])

    with _get_db_connection() as conn:
        cursor = conn.execute(
            f"UPDATE resumes SET {', '.join(set_clauses)} WHERE id = ? AND oid = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise ProfileNotFoundError("Resume not found")
        row = conn.execute(
            "SELECT * FROM resumes WHERE id = ? AND oid = ?",
            (resume_id, oid),
        ).fetchone()
    return _row_to_resume(row)


def delete_achievement_for_user(oid: str, achievement_id: int) -> None:
    _delete_row_by_id_for_oid(
        table="achievements",
        row_id=achievement_id,
        oid=oid,
        not_found_message="Achievement not found",
    )


def delete_education_for_user(oid: str, education_id: int) -> None:
    _delete_row_by_id_for_oid(
        table="educations",
        row_id=education_id,
        oid=oid,
        not_found_message="Education not found",
    )


def delete_resume_for_user(oid: str, resume_id: int) -> None:
    _delete_row_by_id_for_oid(
        table="resumes",
        row_id=resume_id,
        oid=oid,
        not_found_message="Resume not found",
    )
