import sqlite3
from datetime import datetime
from typing import Any, Optional


class ProfileValidationError(Exception):
    pass


_db_path = "careersynth.db"


def configure_profile_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_date(value: Optional[str], field_name: str, allow_null: bool = False) -> Optional[str]:
    if value is None and allow_null:
        return None
    if allow_null and isinstance(value, str) and not value.strip():
        return None
    if value is None:
        raise ProfileValidationError(f"{field_name} is required")

    normalized_value = value.strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(normalized_value, fmt)
            return parsed.strftime("%d-%m-%Y")
        except ValueError:
            continue
    raise ProfileValidationError(f"{field_name} must be in DD-MM-YYYY or YYYY-MM-DD format")


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
