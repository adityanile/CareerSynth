from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_list_column() -> Column:
    return Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)


class ProjectRecord(SQLModel, table=True):
    __tablename__ = "projects"
    __table_args__ = (Index("idx_projects_oid", "oid"),)

    id: int | None = Field(default=None, primary_key=True)
    oid: str = Field(sa_column=Column(String, nullable=False, index=False))
    name: str = Field(sa_column=Column(String, nullable=False))
    tech_stack: list[str] = Field(default_factory=list, sa_column=_json_list_column())
    urls: list[str] = Field(default_factory=list, sa_column=_json_list_column())
    description: str = Field(sa_column=Column(String, nullable=False))
    tags: list[str] = Field(default_factory=list, sa_column=_json_list_column())
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))


class ExperienceRecord(SQLModel, table=True):
    __tablename__ = "experiences"
    __table_args__ = (
        Index("idx_experiences_oid", "oid"),
        Index("idx_experiences_position", "position"),
    )

    id: int | None = Field(default=None, primary_key=True)
    oid: str = Field(sa_column=Column(String, nullable=False))
    company_name: str = Field(sa_column=Column(String, nullable=False))
    start_date: str = Field(sa_column=Column(String, nullable=False))
    end_date: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    position: str = Field(sa_column=Column(String, nullable=False))
    description: str = Field(sa_column=Column(String, nullable=False))
    location: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))


class AchievementRecord(SQLModel, table=True):
    __tablename__ = "achievements"
    __table_args__ = (
        Index("idx_achievements_oid", "oid"),
        Index("idx_achievements_org", "organisation"),
    )

    id: int | None = Field(default=None, primary_key=True)
    oid: str = Field(sa_column=Column(String, nullable=False))
    name: str = Field(sa_column=Column(String, nullable=False))
    link: str = Field(sa_column=Column(String, nullable=False))
    organisation: str = Field(sa_column=Column(String, nullable=False))
    date: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))


class EducationRecord(SQLModel, table=True):
    __tablename__ = "educations"
    __table_args__ = (
        Index("idx_educations_oid", "oid"),
        Index("idx_educations_degree_name", "degree_name"),
    )

    id: int | None = Field(default=None, primary_key=True)
    oid: str = Field(sa_column=Column(String, nullable=False))
    degree_name: str = Field(sa_column=Column(String, nullable=False))
    location: str = Field(sa_column=Column(String, nullable=False))
    start_year: str = Field(sa_column=Column(String, nullable=False))
    end_year: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    cgpa_or_percentage: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))


class ResumeRecord(SQLModel, table=True):
    __tablename__ = "resumes"
    __table_args__ = (
        Index("idx_resumes_oid", "oid"),
        Index("idx_resumes_name", "resume_name"),
    )

    id: int | None = Field(default=None, primary_key=True)
    oid: str = Field(sa_column=Column(String, nullable=False))
    user_reference: str = Field(sa_column=Column(String, nullable=False))
    resume_name: str = Field(sa_column=Column(String, nullable=False))
    resume_description: str = Field(sa_column=Column(String, nullable=False))
    resume: str = Field(sa_column=Column(String, nullable=False))
    created_on: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now))
