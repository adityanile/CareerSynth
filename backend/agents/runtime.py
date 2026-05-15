import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from agent_framework import Agent, SkillsProvider
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
from agents.tools.mem0_retrieve_tool import retrieve_from_mem0_tool
from agents.context import (
    require_current_oid,
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

try:
    from agent_framework.mem0 import Mem0ContextProvider
except Exception:
    Mem0ContextProvider = None


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
- For user questions about their own background data (projects, experience, achievements, education), always call the matching `query_*` tool and always call `retrieve` in the same turn before answering, regardless of whether `query_*` returned data.
- For user-history or preference recall questions ("what do you know about me", "what did I tell you before"), call `retrieve` first.
- If you are uncertain about any user-specific fact, preference, history, goals, or profile detail needed to answer, call `retrieve` before responding.
- Before answering questions about the user's profile, interests, strengths, fit, or recommendations, decide which profile query tools are needed and call them first.
- Do not answer user-specific background/career-fit questions from assumptions or generic memory when relevant query tools exist.
- For broad recommendation questions (for example: best career options for me), call all relevant query tools first:
  - `query_projects`
  - `query_experiences`
  - `query_achievements`
  - `query_educations`
- For focused questions, call the matching query tool(s) before answering:
  - "what projects I love" -> `query_projects`
  - experience-based question -> `query_experiences`
  - achievements-based question -> `query_achievements`
  - education-based question -> `query_educations`
- If query tool results are empty or insufficient, explicitly say what data is missing and ask a targeted follow-up instead of replying "I don't know".
- Never say "I don't know", "I am not sure", or equivalent uncertainty until after you have tried relevant query tool(s) and `retrieve`.
- If both domain query tool(s) and `retrieve` are relevant, call domain query tool(s) first, then call `retrieve` before finalizing the response.
- Never ask the user for `oid` for these operations. It is injected from authenticated request context.
- Do not claim an operation succeeded unless the corresponding tool call succeeds.

Required fields before create tool calls:
- `add_project_to_resume`: `projects` list of objects with `projectName`, `description`, `techStack`
- `add_experience_to_resume`: `experiences` list of objects with `companyName`, `position`, `description`, `startDate`, `location` (optional `endDate`)
- `add_achievement_to_resume`: `achievements` list of objects with `name`, `organisation`, `date`, `link`
- `add_education_to_resume`: `educations` list of objects with `degreeName`, `location`, `startYear`, `endYear` (optional), `cgpaOrPercentage`
- `add_summary`: `summary` string
- `add_skills`: `skills` list of strings
- `add_profile`: `profile` with `name`, `role`, `contact`, `location`, `linkedinUrl`, `additionalUrls`
- `create_project`: `name`, `description`, `tech_stack`, `urls`, `tags`
- `create_experience`: `company_name`, `position`, `start_date`, `end_date` (nullable), `description`, `location`
- `create_achievement`: `name`, `link`, `organisation`, `date`
- `create_education`: `degree_name`, `location`, `start_year`, `end_year` (nullable), `cgpa_or_percentage`
- If required fields are missing or ambiguous, ask only for those missing/ambiguous fields.

Resume behavior:
- For requests to create or refine a resume from current state, first load and follow the `resume-from-snapshot` skill guidance.
- Treat the shared state snapshot (`profile`, `summary`, `skills`, `projects`, `experiences`, `achievements`, `educations`) as source of truth for resume drafting.
- If key snapshot sections needed for the requested resume are missing, ask targeted follow-up questions for only those missing sections.
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
        "tool_argument": "projects",
    },
    "experiences": {
        "tool": "add_experience_to_resume",
        "tool_argument": "experiences",
    },
    "achievements": {
        "tool": "add_achievement_to_resume",
        "tool_argument": "achievements",
    },
    "educations": {
        "tool": "add_education_to_resume",
        "tool_argument": "educations",
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


if Mem0ContextProvider is not None:
    class OidScopedMem0ContextProvider(Mem0ContextProvider):
        """Scope mem0 memory to the authenticated user id for each request run."""

        async def before_run(self, **kwargs: Any) -> None:
            # Intentionally disabled: memory retrieval is handled explicitly via `retrieve` tool.
            return None

        async def after_run(self, **kwargs: Any) -> None:
            self.user_id = require_current_oid()
            await super().after_run(**kwargs)


def _build_openai_client() -> OpenAIChatCompletionClient:
    settings = get_settings()
    return OpenAIChatCompletionClient(
        model=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )


def _build_agent_framework_agent() -> AgentFrameworkAgent:
    settings = get_settings()
    skills_provider = SkillsProvider.from_paths(
        skill_paths=str(Path(__file__).parent / "skills"),
    )
    context_providers: list[Any] = [skills_provider]
    if Mem0ContextProvider is not None:
        mem0_provider = OidScopedMem0ContextProvider(
            source_id="mem0",
            api_key=settings.mem0_api_key,
            application_id=settings.mem0_application_id,
        )
        context_providers.append(mem0_provider)

    agent = Agent(
        client=_build_openai_client(),
        instructions=MAIN_AGENT_INSTRUCTIONS,
        name="main",
        middleware=[ToolCallSequenceRepairMiddleware()],
        context_providers=context_providers,
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
            retrieve_from_mem0_tool,
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
