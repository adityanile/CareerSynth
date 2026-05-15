import json
from collections.abc import AsyncGenerator
from agent_framework import Agent
from agent_framework.ag_ui import AgentFrameworkAgent, add_agent_framework_fastapi_endpoint
from agent_framework.openai import OpenAIChatCompletionClient
from fastapi import Depends, FastAPI, HTTPException, Request

from agents.tools.agent_profile_tools import (
    create_achievement_from_context_tool,
    create_education_from_context_tool,
    create_experience_from_context_tool,
    query_achievements_from_context_tool,
    query_educations_from_context_tool,
    query_experiences_from_context_tool,
)
from agents.tools.agent_project_tools import (
    create_project_from_context_tool,
    query_projects_from_context_tool,
)
from agents.context import (
    reset_current_oid,
    reset_current_thread_id,
    set_current_oid,
    set_current_thread_id,
)
from core.auth import authorize_and_get_oid
from core.settings import get_settings
from domain.models import ResumeState
from agents.tools.resume_pdf_tool import generate_resume_pdf
from agents.tools.resume_state_tools import (
    add_achievement_to_resume_tool,
    add_education_to_resume_tool,
    add_experience_to_resume_tool,
    add_profile_tool,
    add_skills_tool,
    add_summary_tool,
    add_project_to_resume_tool,
)
from agents.middleware.tool_call_sequence_middleware import ToolCallSequenceRepairMiddleware


MAIN_AGENT_INSTRUCTIONS = """
You are the main CareerSynth agent.

Tool usage rules:
- Intent routing is strict and mutually exclusive:
- If the user explicitly says "add to resume", "put in resume", "include in resume", use only the matching resume-state tool:
  - `add_project_to_resume`
  - `add_experience_to_resume`
  - `add_achievement_to_resume`
  - `add_education_to_resume`
  - `add_summary`
  - `add_skills`
  - `add_profile`
- If the user explicitly says "create", "save", "store", or "add" for project/experience/achievement/education in system/database terms (and does not say resume), use only the matching create tool:
  - `create_project`
  - `create_experience`
  - `create_achievement`
  - `create_education`
- Never use a create tool when the user explicitly requested resume.
- Never use a resume-state add tool when the user explicitly requested create/save/store in system/database terms.
- If both intents appear in the same request, ask a single clarification question before calling tools.
- Handle project queries with `query_projects`.
- Handle experience queries with `query_experiences`.
- Handle achievement queries with `query_achievements`.
- Handle education queries with `query_educations`.
- Never ask the user for `oid` for these operations. It is injected from authenticated request context.
- Do not claim an operation succeeded unless the corresponding tool call succeeds.

Required fields before create tool calls:
- `add_project_to_resume`: `project` with `projectName`, `description`, `techStack`
- `add_experience_to_resume`: `experience` with `companyName`, `position`, `description`, `startDate`, `location` (optional `endDate`)
- `add_achievement_to_resume`: `achievement` with `name`, `organisation`, `date`, `link`
- `add_education_to_resume`: `education` with `degreeName`, `location`, `startYear`, `endYear` (optional), `cgpaOrPercentage`
- `add_summary`: `summary` string
- `add_skills`: `skills` list of strings
- `add_profile`: `profile` with `name`, `role`, `contact`, `location`, `linkedinUrl`, `additionalUrls`
- `create_project`: `name`, `description`, `tech_stack`, `urls`, `tags`
- `create_experience`: `company_name`, `position`, `start_date`, `end_date` (nullable), `description`, `location`
- `create_achievement`: `name`, `link`, `organisation`, `date`
- `create_education`: `degree_name`, `location`, `start_year`, `end_year` (nullable), `cgpa_or_percentage`
- If required fields are missing or ambiguous, ask only for those missing/ambiguous fields.

Resume behavior:
- For resume drafting, refinement, LaTeX generation, and PDF generation, use `generate_resume_pdf` when needed.
- For `generate_resume_pdf`, pass full final LaTeX source and any explicit user constraints already requested.

Response behavior:
- Keep user-facing responses concise and execution-focused.
- After tool completion, summarize the result and confirm next action.
- If the current user request is fully done, end your final response with exactly: Task complete.
"""

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
    "educations": {
        "tool": "add_education_to_resume",
        "tool_argument": "education",
    },
    "summary": {
        "tool": "add_summary",
        "tool_argument": "summary",
    },
    "skills": {
        "tool": "add_skills",
        "tool_argument": "skills",
    },
    "profile": {
        "tool": "add_profile",
        "tool_argument": "profile",
    },
}


def _build_openai_client() -> OpenAIChatCompletionClient:
    settings = get_settings()
    return OpenAIChatCompletionClient(
        model=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )


def _build_agent_framework_agent() -> AgentFrameworkAgent:
    agent = Agent(
        client=_build_openai_client(),
        instructions=MAIN_AGENT_INSTRUCTIONS,
        name="main",
        middleware=[ToolCallSequenceRepairMiddleware()],
        tools=[
            generate_resume_pdf,
            add_project_to_resume_tool,
            add_experience_to_resume_tool,
            add_achievement_to_resume_tool,
            add_education_to_resume_tool,
            add_summary_tool,
            add_skills_tool,
            add_profile_tool,
            create_project_from_context_tool,
            query_projects_from_context_tool,
            create_experience_from_context_tool,
            query_experiences_from_context_tool,
            create_achievement_from_context_tool,
            query_achievements_from_context_tool,
            create_education_from_context_tool,
            query_educations_from_context_tool,
        ],
    )

    return AgentFrameworkAgent(
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
            "educations": {
                "type": "array",
                "description": "Current list of resume education entries",
                "items": {"type": "object"},
            },
            "summary": {
                "type": "string",
                "description": "Current resume summary statement",
            },
            "skills": {
                "type": "array",
                "description": "Current list of resume skills",
                "items": {"type": "string"},
            },
            "profile": {
                "type": "object",
                "description": "Current resume profile block",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "contact": {"type": "string"},
                    "location": {"type": "string"},
                    "linkedinUrl": {"type": "string"},
                    "additionalUrls": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        predict_state_config=PREDICTED_STATE_CONFIG,
        require_confirmation=False,
    )


def _default_resume_state() -> dict:
    return ResumeState().model_dump()


async def agui_auth_context(request: Request) -> AsyncGenerator[None, None]:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    oid = authorize_and_get_oid(request)
    thread_id = "default"
    try:
        raw_body = await request.body()
        if raw_body:
            payload = json.loads(raw_body)
            if isinstance(payload, dict):
                thread_id_value = payload.get("thread_id") or payload.get("threadId")
                if thread_id_value is not None:
                    normalized_thread_id = str(thread_id_value).strip()
                    if normalized_thread_id:
                        thread_id = normalized_thread_id
    except Exception:
        thread_id = "default"

    oid_token = set_current_oid(oid)
    thread_id_token = set_current_thread_id(thread_id)
    try:
        yield
    finally:
        reset_current_thread_id(thread_id_token)
        reset_current_oid(oid_token)


def register_agui_endpoint(app: FastAPI) -> None:
    add_agent_framework_fastapi_endpoint(
        app,
        _build_agent_framework_agent(),
        "/",
        default_state=_default_resume_state(),
        dependencies=[Depends(agui_auth_context)],
    )
