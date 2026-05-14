import json
import sqlite3
from typing import Any, Optional

class ProjectValidationError(Exception):
    pass


class ProjectNotFoundError(Exception):
    pass


_db_path = "careersynth.db"


def configure_project_db(db_path: str) -> None:
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


def _row_to_project(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "techStack": json.loads(row["tech_stack"]),
        "urls": json.loads(row["urls"]),
        "description": row["description"],
        "tags": json.loads(row["tags"]),
        "summary": row["summary"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


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
    summary: str,
) -> dict[str, Any]:
    normalized_name = name.strip()
    normalized_description = description.strip()
    normalized_summary = summary.strip()

    if not normalized_name or not normalized_description or not normalized_summary:
        raise ProjectValidationError("name, description and summary are required")

    normalized_tech_stack = _normalize_string_list(tech_stack, "techStack")
    normalized_urls = _normalize_string_list(urls, "urls")
    normalized_tags = _normalize_string_list(tags, "tags")

    with _get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO projects (oid, name, tech_stack, urls, description, tags, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                oid,
                normalized_name,
                json.dumps(normalized_tech_stack),
                json.dumps(normalized_urls),
                normalized_description,
                json.dumps(normalized_tags),
                normalized_summary,
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

    if "summary" in updates:
        value = (updates["summary"] or "").strip()
        if not value:
            raise ProjectValidationError("summary cannot be empty")
        set_clauses.append("summary = ?")
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
