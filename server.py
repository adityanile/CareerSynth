import os
import sqlite3
from collections.abc import AsyncGenerator
from typing import Any, Optional

from dotenv import load_dotenv
from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.ag_ui import AgentFrameworkAgent, add_agent_framework_fastapi_endpoint
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi_microsoft_identity import AuthError, initialize, requires_auth, validate_scope

from agent_profile_tools import (
    create_achievement_from_context_tool,
    create_experience_from_context_tool,
    query_achievements_from_context_tool,
    query_experiences_from_context_tool,
)
from agent_project_tools import create_project_from_context_tool, query_projects_from_context_tool
from agent_request_context import reset_current_oid, set_current_oid
from models import (
    AchievementCreate,
    AchievementPatch,
    ExperienceCreate,
    ExperiencePatch,
    ProjectCreate,
    ProjectPatch,
    ResumeState,
)
from project_tools import (
    ProjectNotFoundError,
    ProjectValidationError,
    configure_project_db,
    create_project_for_user,
    delete_project_for_user,
    get_project_for_user,
    get_projects_by_tag_for_user,
    list_projects_for_user,
    update_project_for_user,
)
from profile_tools import (
    ProfileValidationError,
    configure_profile_db,
    create_achievement_for_user,
    create_experience_for_user,
    list_achievements_for_user,
    list_experiences_for_user,
)
from resume_state_tools import (
    add_achievement_to_resume_tool,
    add_experience_to_resume_tool,
    add_project_to_resume_tool,
)
from resume_pdf_tool import generate_resume_pdf
from tool_call_sequence_middleware import ToolCallSequenceRepairMiddleware

from fastapi_microsoft_identity import auth_service as token_auth_service

load_dotenv()

entra_tenant_id = os.getenv("ENTRA_TENANT_ID")
entra_client_id = os.getenv("ENTRA_CLIENT_ID")

if not entra_tenant_id or not entra_client_id:
    raise RuntimeError("ENTRA_TENANT_ID and ENTRA_CLIENT_ID are required.")

initialize(tenant_id_=entra_tenant_id, client_id_=entra_client_id)
entra_required_scope = os.getenv("ENTRA_REQUIRED_SCOPE", "User")
db_path = os.getenv("SQLITE_DB_PATH", "careersynth.db")

client = OpenAIChatCompletionClient(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

main_agent_instructions = """
You are the main CareerSynth agent.

Tool usage rules:
- Intent routing is strict and mutually exclusive:
- If the user explicitly says "add to resume", "put in resume", "include in resume", or "save to resume", use only the matching resume-state tool:
  - `add_project_to_resume`
  - `add_experience_to_resume`
  - `add_achievement_to_resume`
- If the user explicitly says "create", "save", "store", or "add" for project/experience/achievement in system/database terms (and does not say resume), use only the matching create tool:
  - `create_project`
  - `create_experience`
  - `create_achievement`
- Never use a create tool when the user explicitly requested resume.
- Never use a resume-state add tool when the user explicitly requested create/save/store in system/database terms.
- If both intents appear in the same request, ask a single clarification question before calling tools.
- Handle project queries with `query_projects`.
- Handle experience queries with `query_experiences`.
- Handle achievement queries with `query_achievements`.
- Never ask the user for `oid` for these operations. It is injected from authenticated request context.
- Do not claim an operation succeeded unless the corresponding tool call succeeds.

Required fields before create tool calls:
- `add_project_to_resume`: `project` with `projectName`, `description`, `techStack`
- `add_experience_to_resume`: `experience` with `companyName`, `position`, `description`, `startDate`, `location` (optional `endDate`)
- `add_achievement_to_resume`: `achievement` with `name`, `organisation`, `date`, `link`
- `create_project`: `name`, `description`, `tech_stack`, `urls`, `tags`
- `create_experience`: `company_name`, `position`, `start_date`, `end_date` (nullable), `description`, `location`
- `create_achievement`: `name`, `link`, `organisation`, `date`
- If required fields are missing or ambiguous, ask only for those missing/ambiguous fields.

Resume behavior:
- For resume drafting, refinement, LaTeX generation, and PDF generation, use `generate_resume_pdf` when needed.
- For `generate_resume_pdf`, pass full final LaTeX source and any explicit user constraints already requested.

Response behavior:
- Keep user-facing responses concise and execution-focused.
- After tool completion, summarize the result and confirm next action.
- If the current user request is fully done, end your final response with exactly: Task complete.
"""

app = FastAPI(title="AG-UI Server")
_default_resume_state_model = ResumeState()
DEFAULT_RESUME_STATE = _default_resume_state_model.model_dump()


agent = Agent(
    client=client,
    instructions=main_agent_instructions,
    name="main",
    middleware=[ToolCallSequenceRepairMiddleware()],
    tools=[
        generate_resume_pdf,
        add_project_to_resume_tool,
        add_experience_to_resume_tool,
        add_achievement_to_resume_tool,
        create_project_from_context_tool,
        query_projects_from_context_tool,
        create_experience_from_context_tool,
        query_experiences_from_context_tool,
        create_achievement_from_context_tool,
        query_achievements_from_context_tool,
    ],
)

PREDICTED_STATE_CONFIG: dict[str, dict[str, str | None]] = {
    "projects": {
        "tool": "add_project_to_resume",
        "tool_argument": "project",
    },
    "experiences": {
        "tool": "add_experience_to_resume",
        "tool_argument": "experience",
    },
    "achievements": {
        "tool": "add_achievement_to_resume",
        "tool_argument": "achievement",
    },
}

agui_agent = AgentFrameworkAgent(
    agent=agent,
    name="CareerSynthAgent",
    description="Maintains and streams the user's resume state snapshot",
    state_schema={
        "projects": {
            "type": "array",
            "description": "Current list of resume projects",
            "items": {"type": "object"},
        },
        "experiences": {
            "type": "array",
            "description": "Current list of resume experiences",
            "items": {"type": "object"},
        },
        "achievements": {
            "type": "array",
            "description": "Current list of resume achievements",
            "items": {"type": "object"},
        },
    },
    predict_state_config=PREDICTED_STATE_CONFIG,
    require_confirmation=False,
)

async def agui_auth_context(request: Request) -> AsyncGenerator[None, None]:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    oid = authorize_and_get_oid(request)
    token = set_current_oid(oid)
    try:
        yield
    finally:
        reset_current_oid(token)


add_agent_framework_fastapi_endpoint(
    app,
    agui_agent,
    "/",
    default_state=DEFAULT_RESUME_STATE,
    dependencies=[Depends(agui_auth_context)],
)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oid TEXT NOT NULL,
                name TEXT NOT NULL,
                tech_stack TEXT NOT NULL DEFAULT '[]',
                urls TEXT NOT NULL DEFAULT '[]',
                description TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_projects_oid ON projects(oid);

            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oid TEXT NOT NULL,
                company_name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                position TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_experiences_oid ON experiences(oid);
            CREATE INDEX IF NOT EXISTS idx_experiences_position ON experiences(position);

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oid TEXT NOT NULL,
                name TEXT NOT NULL,
                link TEXT NOT NULL,
                organisation TEXT NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_achievements_oid ON achievements(oid);
            CREATE INDEX IF NOT EXISTS idx_achievements_org ON achievements(organisation);
            """
        )

@app.on_event("startup")
def on_startup() -> None:
    init_db()
    configure_project_db(db_path)
    configure_profile_db(db_path)


def model_to_partial_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def validate_date_text(value: Optional[str], field_name: str, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if allow_null and isinstance(value, str) and not value.strip():
        return
    if value is None:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    normalized_value = value.strip()
    if not normalized_value:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")


def get_oid_or_401(request: Request) -> str:
    token_claims = token_auth_service.get_token_claims(request)
    oid = token_claims.get("oid")
    if not oid:
        raise HTTPException(status_code=401, detail="Missing oid claim in token")
    return str(oid)

def authorize_and_get_oid(request: Request) -> str:
    try:
        validate_scope(required_scope=entra_required_scope, request=request)
    except AuthError as exc:
        raise HTTPException(status_code=403, detail=exc.error_msg) from exc
    return get_oid_or_401(request)


def row_to_experience(row: sqlite3.Row) -> dict[str, Any]:
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


def row_to_achievement(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "link": row["link"],
        "organisation": row["organisation"],
        "date": row["date"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


@app.get("/health")
def home() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/test")
@requires_auth
async def auth_test(request: Request) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    return {"message": "You are authenticated", "oid": oid}


@app.get("/api/projects")
@requires_auth
async def list_projects(
    request: Request,
    tag: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    tech: Optional[str] = Query(default=None),
    techs: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    items = list_projects_for_user(oid, tag=tag, tags=tags, tech=tech, techs=techs, name=name)
    return {"items": items}


@app.post("/api/projects", status_code=201)
@requires_auth
async def create_project(request: Request, payload: ProjectCreate) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return create_project_for_user(
            oid=oid,
            name=payload.name,
            tech_stack=payload.techStack,
            urls=payload.urls,
            description=payload.description,
            tags=payload.tags,
        )
    except ProjectValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/projects/{project_id}")
@requires_auth
async def get_project(request: Request, project_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return get_project_for_user(oid=oid, project_id=project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/projects/by-tag/{tag}")
@requires_auth
async def get_projects_by_tag(request: Request, tag: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        items = get_projects_by_tag_for_user(oid=oid, tag=tag)
        return {"items": items}
    except ProjectValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/projects/by-tech/{tech}")
@requires_auth
async def get_projects_by_tech(request: Request, tech: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    tech_value = tech.strip()
    if not tech_value:
        raise HTTPException(status_code=400, detail="tech is required")
    items = list_projects_for_user(oid=oid, tech=tech_value)
    return {"items": items}


@app.patch("/api/projects/{project_id}")
@requires_auth
async def patch_project(request: Request, project_id: int, payload: ProjectPatch) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    updates = model_to_partial_dict(payload)
    try:
        return update_project_for_user(oid=oid, project_id=project_id, updates=updates)
    except ProjectValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/projects/{project_id}", status_code=204)
@requires_auth
async def delete_project(request: Request, project_id: int) -> None:
    oid = authorize_and_get_oid(request)
    try:
        delete_project_for_user(oid=oid, project_id=project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/experiences")
@requires_auth
async def list_experiences(
    request: Request,
    position: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    items = list_experiences_for_user(oid=oid, position=position)
    return {"items": items}


@app.post("/api/experiences", status_code=201)
@requires_auth
async def create_experience(request: Request, payload: ExperienceCreate) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return create_experience_for_user(
            oid=oid,
            company_name=payload.companyName,
            start_date=payload.startDate,
            end_date=payload.endDate,
            position=payload.position,
            description=payload.description,
            location=payload.location,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/experiences/{experience_id}")
@requires_auth
async def get_experience(request: Request, experience_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM experiences WHERE id = ? AND oid = ?",
            (experience_id, oid),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Experience not found")
    return row_to_experience(row)


@app.get("/api/experiences/by-position/{position}")
@requires_auth
async def get_experiences_by_position(request: Request, position: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    position_value = position.strip()
    if not position_value:
        raise HTTPException(status_code=400, detail="position is required")
    items = list_experiences_for_user(oid=oid, position=position_value)
    return {"items": items}


@app.get("/api/experiences/by-company/{company_name}")
@requires_auth
async def get_experiences_by_company(request: Request, company_name: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    company_value = company_name.strip()
    if not company_value:
        raise HTTPException(status_code=400, detail="company_name is required")
    items = list_experiences_for_user(oid=oid, company_name=company_value)
    return {"items": items}


@app.patch("/api/experiences/{experience_id}")
@requires_auth
async def patch_experience(
    request: Request,
    experience_id: int,
    payload: ExperiencePatch,
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    updates = model_to_partial_dict(payload)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    set_clauses: list[str] = []
    params: list[Any] = []

    if "companyName" in updates:
        value = (updates["companyName"] or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="companyName cannot be empty")
        set_clauses.append("company_name = ?")
        params.append(value)

    if "startDate" in updates:
        validate_date_text(updates["startDate"], "startDate")
        set_clauses.append("start_date = ?")
        params.append(updates["startDate"])

    if "endDate" in updates:
        validate_date_text(updates["endDate"], "endDate", allow_null=True)
        set_clauses.append("end_date = ?")
        params.append(updates["endDate"])

    if "position" in updates:
        value = (updates["position"] or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="position cannot be empty")
        set_clauses.append("position = ?")
        params.append(value)

    if "description" in updates:
        value = (updates["description"] or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="description cannot be empty")
        set_clauses.append("description = ?")
        params.append(value)

    if "location" in updates:
        value = (updates["location"] or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="location cannot be empty")
        set_clauses.append("location = ?")
        params.append(value)

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([experience_id, oid])

    with get_db_connection() as conn:
        cursor = conn.execute(
            f"UPDATE experiences SET {', '.join(set_clauses)} WHERE id = ? AND oid = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Experience not found")
        row = conn.execute(
            "SELECT * FROM experiences WHERE id = ? AND oid = ?",
            (experience_id, oid),
        ).fetchone()

    return row_to_experience(row)


@app.delete("/api/experiences/{experience_id}", status_code=204)
@requires_auth
async def delete_experience(request: Request, experience_id: int) -> None:
    oid = authorize_and_get_oid(request)

    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM experiences WHERE id = ? AND oid = ?",
            (experience_id, oid),
        )

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Experience not found")


@app.get("/api/achievements")
@requires_auth
async def list_achievements(
    request: Request,
    organisation: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    items = list_achievements_for_user(oid=oid, organisation=organisation, name=name)
    return {"items": items}


@app.post("/api/achievements", status_code=201)
@requires_auth
async def create_achievement(request: Request, payload: AchievementCreate) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return create_achievement_for_user(
            oid=oid,
            name=payload.name,
            link=payload.link,
            organisation=payload.organisation,
            date=payload.date,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/achievements/{achievement_id}")
@requires_auth
async def get_achievement(request: Request, achievement_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM achievements WHERE id = ? AND oid = ?",
            (achievement_id, oid),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return row_to_achievement(row)


@app.get("/api/achievements/by-organisation/{organisation}")
@requires_auth
async def get_achievements_by_organisation(request: Request, organisation: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    organisation_value = organisation.strip()
    if not organisation_value:
        raise HTTPException(status_code=400, detail="organisation is required")
    items = list_achievements_for_user(oid=oid, organisation=organisation_value)
    return {"items": items}


@app.get("/api/achievements/by-name/{name}")
@requires_auth
async def get_achievements_by_name(request: Request, name: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    name_value = name.strip()
    if not name_value:
        raise HTTPException(status_code=400, detail="name is required")
    items = list_achievements_for_user(oid=oid, name=name_value)
    return {"items": items}


@app.patch("/api/achievements/{achievement_id}")
@requires_auth
async def patch_achievement(
    request: Request,
    achievement_id: int,
    payload: AchievementPatch,
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    updates = model_to_partial_dict(payload)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    set_clauses: list[str] = []
    params: list[Any] = []

    if "name" in updates:
        value = (updates["name"] or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="name cannot be empty")
        set_clauses.append("name = ?")
        params.append(value)

    if "link" in updates:
        value = (updates["link"] or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="link cannot be empty")
        set_clauses.append("link = ?")
        params.append(value)

    if "organisation" in updates:
        value = (updates["organisation"] or "").strip()
        if not value:
            raise HTTPException(status_code=400, detail="organisation cannot be empty")
        set_clauses.append("organisation = ?")
        params.append(value)

    if "date" in updates:
        validate_date_text(updates["date"], "date")
        set_clauses.append("date = ?")
        params.append(updates["date"])

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([achievement_id, oid])

    with get_db_connection() as conn:
        cursor = conn.execute(
            f"UPDATE achievements SET {', '.join(set_clauses)} WHERE id = ? AND oid = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Achievement not found")
        row = conn.execute(
            "SELECT * FROM achievements WHERE id = ? AND oid = ?",
            (achievement_id, oid),
        ).fetchone()

    return row_to_achievement(row)


@app.delete("/api/achievements/{achievement_id}", status_code=204)
@requires_auth
async def delete_achievement(request: Request, achievement_id: int) -> None:
    oid = authorize_and_get_oid(request)

    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM achievements WHERE id = ? AND oid = ?",
            (achievement_id, oid),
        )

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Achievement not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8888, reload=True)
