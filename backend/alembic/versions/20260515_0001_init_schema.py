"""init careersynth schema

Revision ID: 20260515_0001
Revises: 
Create Date: 2026-05-15 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260515_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("oid", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tech_stack", sa.JSON(), nullable=False),
        sa.Column("urls", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_projects_oid", "projects", ["oid"])

    op.create_table(
        "experiences",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("oid", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("start_date", sa.String(), nullable=False),
        sa.Column("end_date", sa.String(), nullable=True),
        sa.Column("position", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_experiences_oid", "experiences", ["oid"])
    op.create_index("idx_experiences_position", "experiences", ["position"])

    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("oid", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("link", sa.String(), nullable=False),
        sa.Column("organisation", sa.String(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_achievements_oid", "achievements", ["oid"])
    op.create_index("idx_achievements_org", "achievements", ["organisation"])

    op.create_table(
        "educations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("oid", sa.String(), nullable=False),
        sa.Column("degree_name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("start_year", sa.String(), nullable=False),
        sa.Column("end_year", sa.String(), nullable=True),
        sa.Column("cgpa_or_percentage", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_educations_oid", "educations", ["oid"])
    op.create_index("idx_educations_degree_name", "educations", ["degree_name"])

    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("oid", sa.String(), nullable=False),
        sa.Column("user_reference", sa.String(), nullable=False),
        sa.Column("resume_name", sa.String(), nullable=False),
        sa.Column("resume_description", sa.String(), nullable=False),
        sa.Column("resume", sa.String(), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_resumes_oid", "resumes", ["oid"])
    op.create_index("idx_resumes_name", "resumes", ["resume_name"])


def downgrade() -> None:
    op.drop_index("idx_resumes_name", table_name="resumes")
    op.drop_index("idx_resumes_oid", table_name="resumes")
    op.drop_table("resumes")

    op.drop_index("idx_educations_degree_name", table_name="educations")
    op.drop_index("idx_educations_oid", table_name="educations")
    op.drop_table("educations")

    op.drop_index("idx_achievements_org", table_name="achievements")
    op.drop_index("idx_achievements_oid", table_name="achievements")
    op.drop_table("achievements")

    op.drop_index("idx_experiences_position", table_name="experiences")
    op.drop_index("idx_experiences_oid", table_name="experiences")
    op.drop_table("experiences")

    op.drop_index("idx_projects_oid", table_name="projects")
    op.drop_table("projects")
