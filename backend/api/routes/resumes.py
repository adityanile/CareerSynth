import os
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import Any, Optional
from urllib.parse import urlparse

from agent_framework import Content, Message
from agent_framework.openai import OpenAIChatClient
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile

from api.utils import model_to_partial_dict
from core.auth import authorize_and_get_oid, requires_auth
from core.settings import get_settings
from domain.models import ParsedResumeOutput, ResumeCreate, ResumeParseTextRequest, ResumePatch
from domain.repository import (
    ProfileNotFoundError,
    ProfileValidationError,
    ProjectValidationError,
    create_achievement_for_user,
    create_education_for_user,
    create_experience_for_user,
    create_project_for_user,
    create_resume_for_user,
    delete_resume_for_user,
    get_resume_for_user,
    list_resumes_for_user,
    update_resume_for_user,
)


router = APIRouter()

_SUPPORTED_RESUME_EXTENSIONS = {".pdf", ".docx"}
_SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}

_RESUME_PARSE_INSTRUCTIONS = """
Extract resume data into strict JSON with these top-level keys:
- projects: list[{projectName, description, techStack}]
- experiences: list[{companyName, position, description, startDate, endDate, pursuing, location}]
- achievements: list[{name, organisation, date, link}]
- educations: list[{degreeName, location, startYear, endYear, pursuing, cgpaOrPercentage}]

Rules:
- Return only schema-valid data.
- Treat certifications, certificates, and licenses as achievements.
- Put each certification as one item in `achievements`:
  - `name`: certification name
  - `organisation`: issuing authority
  - `date`: issue/earned date (or best available date string)
  - `link`: credential URL (empty string if not available)
- For ongoing education/experience, set `pursuing` to true.
- If `pursuing` is true, `endYear`/`endDate` can be null or empty.
- If data is missing, use empty string for scalar fields, null for optional endDate/endYear, and empty list for arrays.
- Do not invent details not present in the resume.
"""


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _extract_blob_name(blob_url: str, container_name: str) -> Optional[str]:
    parsed = urlparse(blob_url.strip())
    if parsed.scheme not in {"http", "https"}:
        return None
    if ".blob.core.windows.net" not in parsed.netloc:
        return None

    path = parsed.path.lstrip("/")
    prefix = f"{container_name}/"
    if not path.startswith(prefix):
        return None

    blob_name = path[len(prefix) :].strip()
    return blob_name or None


def _delete_resume_blob_if_needed(blob_url: str) -> None:
    if not blob_url.strip():
        return

    container_name = _required_env("AZURE_STORAGE_CONTAINER_NAME")
    blob_name = _extract_blob_name(blob_url, container_name)
    if not blob_name:
        return

    account_name = _required_env("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = _required_env("AZURE_STORAGE_ACCOUNT_KEY")
    account_url = f"https://{account_name}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=account_key)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    try:
        blob_client.delete_blob(delete_snapshots="include")
    except ResourceNotFoundError:
        # Already deleted is treated as clean.
        return


def _normalize_filename(file_name: str) -> str:
    normalized = (file_name or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")
    return normalized


def _file_extension(file_name: str) -> str:
    dot_index = file_name.rfind(".")
    if dot_index == -1:
        return ""
    return file_name[dot_index:].lower()


def _validate_resume_upload(file_name: str, content_type: str) -> str:
    extension = _file_extension(file_name)
    if extension not in _SUPPORTED_RESUME_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    normalized_content_type = (content_type or "").strip().lower()
    if normalized_content_type and normalized_content_type not in _SUPPORTED_MIME_TYPES:
        # Postman frequently sends application/octet-stream for binary file uploads.
        # Keep extension as the primary guard and avoid false rejections.
        pass

    return extension


def _extract_docx_text(file_bytes: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as archive:
            document_xml = archive.read("word/document.xml")
    except Exception as exc:
        raise ValueError("Invalid DOCX file.") from exc

    root = ET.fromstring(document_xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        texts = [text_node.text for text_node in paragraph.findall(".//w:t", namespace) if text_node.text]
        if texts:
            paragraphs.append("".join(texts))

    extracted_text = "\n".join(paragraphs).strip()
    if not extracted_text:
        raise ValueError("No readable text found in DOCX.")
    return extracted_text


def _build_resume_parser_agent():
    settings = get_settings()
    if (
        not settings.azure_openai_deployment
        or not settings.azure_openai_endpoint
        or not settings.azure_openai_api_key
    ):
        raise RuntimeError(
            "Missing Azure OpenAI configuration. "
            "Set AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_API_KEY."
        )

    client = OpenAIChatClient(
        model=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
    return client.as_agent(
        name="ResumeParserAgent",
        instructions=_RESUME_PARSE_INSTRUCTIONS,
    )


async def _parse_resume_from_text(resume_text: str) -> ParsedResumeOutput:
    parser_agent = _build_resume_parser_agent()
    user_message = Message(
        role="user",
        contents=[
            Content.from_text(
                text=(
                    "Parse this resume text and extract structured details.\n\n"
                    f"{resume_text}"
                )
            )
        ],
    )

    response = await parser_agent.run(
        [user_message],
        options={"response_format": ParsedResumeOutput},
    )

    if isinstance(response.value, ParsedResumeOutput):
        return response.value
    if response.value:
        return ParsedResumeOutput.model_validate(response.value)
    raise RuntimeError("Parser did not return structured output.")


async def _parse_resume_from_pdf(file_name: str, file_bytes: bytes) -> ParsedResumeOutput:
    parser_agent = _build_resume_parser_agent()
    user_message = Message(
        role="user",
        contents=[
            Content.from_text(text="Extract structured resume information from this PDF."),
            Content.from_data(
                data=file_bytes,
                media_type="application/pdf",
                additional_properties={"filename": file_name},
            ),
        ],
    )

    response = await parser_agent.run(
        [user_message],
        options={"response_format": ParsedResumeOutput},
    )

    if isinstance(response.value, ParsedResumeOutput):
        return response.value
    if response.value:
        return ParsedResumeOutput.model_validate(response.value)
    raise RuntimeError("Parser did not return structured output.")


@router.get("/api/resumes")
@requires_auth
async def list_resumes(
    request: Request,
    resume_name: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    items = list_resumes_for_user(oid=oid, resume_name=resume_name)
    return {"items": items}


@router.post("/api/resumes", status_code=201)
@requires_auth
async def create_resume(request: Request, payload: ResumeCreate) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return create_resume_for_user(
            oid=oid,
            resume_name=payload.resumeName,
            resume_description=payload.resumeDescription,
            resume=payload.resume,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/resumes/{resume_id}")
@requires_auth
async def get_resume(request: Request, resume_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return get_resume_for_user(oid=oid, resume_id=resume_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/api/resumes/{resume_id}")
@requires_auth
async def patch_resume(request: Request, resume_id: int, payload: ResumePatch) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    updates = model_to_partial_dict(payload)
    try:
        return update_resume_for_user(oid=oid, resume_id=resume_id, updates=updates)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/resumes/{resume_id}", status_code=204)
@requires_auth
async def delete_resume(request: Request, resume_id: int) -> None:
    oid = authorize_and_get_oid(request)
    try:
        resume = get_resume_for_user(oid=oid, resume_id=resume_id)
        try:
            _delete_resume_blob_if_needed(resume.get("resume", ""))
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to delete resume blob: {exc}",
            ) from exc
        delete_resume_for_user(oid=oid, resume_id=resume_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/resumes/parse")
@requires_auth
async def parse_resume(
    request: Request,
    file: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    authorize_and_get_oid(request)
    if file is not None:
        file_name = _normalize_filename(file.filename or "")
        extension = _validate_resume_upload(file_name, file.content_type or "")
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        try:
            if extension == ".pdf":
                parsed = await _parse_resume_from_pdf(file_name, file_bytes)
            else:
                extracted_text = _extract_docx_text(file_bytes)
                parsed = await _parse_resume_from_text(extracted_text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to parse resume: {exc}") from exc

        return parsed.model_dump()

    try:
        payload = ResumeParseTextRequest.model_validate(await request.json())
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Provide either a PDF/DOCX file upload or a JSON body with `text`.",
        ) from exc

    resume_text = payload.text.strip()
    if not resume_text:
        raise HTTPException(status_code=400, detail="text cannot be empty.")

    try:
        parsed = await _parse_resume_from_text(resume_text)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to parse resume text: {exc}") from exc

    return parsed.model_dump()


@router.post("/api/resumes/parse/save")
@requires_auth
async def save_parsed_resume_to_system(
    request: Request,
    payload: ParsedResumeOutput,
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)

    created_projects: list[dict[str, Any]] = []
    created_experiences: list[dict[str, Any]] = []
    created_achievements: list[dict[str, Any]] = []
    created_educations: list[dict[str, Any]] = []
    validation_issues: list[str] = []

    try:
        for index, project in enumerate(payload.projects, start=1):
            name = (project.projectName or "").strip()
            description = (project.description or "").strip()
            missing_fields: list[str] = []
            if not name:
                missing_fields.append("projectName")
            if not description:
                missing_fields.append("description")
            if missing_fields:
                validation_issues.append(f"projects[{index}]: {', '.join(missing_fields)}")
                continue
            created_projects.append(
                create_project_for_user(
                    oid=oid,
                    name=name,
                    description=description,
                    tech_stack=project.techStack or [],
                    urls=[],
                    tags=[],
                )
            )
        for index, experience in enumerate(payload.experiences, start=1):
            company_name = (experience.companyName or "").strip()
            position = (experience.position or "").strip()
            description = (experience.description or "").strip()
            start_date = (experience.startDate or "").strip()
            end_date = (experience.endDate or "").strip()
            pursuing = bool(experience.pursuing)
            location = (experience.location or "").strip()
            missing_fields = []
            if not company_name:
                missing_fields.append("companyName")
            if not position:
                missing_fields.append("position")
            if not description:
                missing_fields.append("description")
            if not start_date:
                missing_fields.append("startDate")
            if not pursuing and not end_date:
                missing_fields.append("endDate (or set pursuing=true)")
            if not location:
                missing_fields.append("location")
            if missing_fields:
                validation_issues.append(f"experiences[{index}]: {', '.join(missing_fields)}")
                continue
            created_experiences.append(
                create_experience_for_user(
                    oid=oid,
                    company_name=company_name,
                    position=position,
                    description=description,
                    start_date=start_date,
                    end_date=end_date or None,
                    location=location,
                )
            )
        for index, achievement in enumerate(payload.achievements, start=1):
            name = (achievement.name or "").strip()
            organisation = (achievement.organisation or "").strip()
            date = (achievement.date or "").strip()
            link = (achievement.link or "").strip()
            missing_fields = []
            if not name:
                missing_fields.append("name")
            if not organisation:
                missing_fields.append("organisation")
            if not date:
                missing_fields.append("date")
            if not link:
                missing_fields.append("link")
            if missing_fields:
                validation_issues.append(f"achievements[{index}]: {', '.join(missing_fields)}")
                continue
            created_achievements.append(
                create_achievement_for_user(
                    oid=oid,
                    name=name,
                    organisation=organisation,
                    date=date,
                    link=link,
                ),
            )
        for index, education in enumerate(payload.educations, start=1):
            degree_name = (education.degreeName or "").strip()
            location = (education.location or "").strip()
            start_year = (education.startYear or "").strip()
            end_year = (education.endYear or "").strip()
            pursuing = bool(education.pursuing)
            cgpa_or_percentage = (education.cgpaOrPercentage or "").strip()
            missing_fields = []
            if not degree_name:
                missing_fields.append("degreeName")
            if not location:
                missing_fields.append("location")
            if not start_year:
                missing_fields.append("startYear")
            if not pursuing and not end_year:
                missing_fields.append("endYear (or set pursuing=true)")
            if not cgpa_or_percentage:
                missing_fields.append("cgpaOrPercentage")
            if missing_fields:
                validation_issues.append(f"educations[{index}]: {', '.join(missing_fields)}")
                continue
            created_educations.append(
                create_education_for_user(
                    oid=oid,
                    degree_name=degree_name,
                    location=location,
                    start_year=start_year,
                    end_year=end_year or None,
                    cgpa_or_percentage=cgpa_or_percentage,
                )
            )
    except (ProjectValidationError, ProfileValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if validation_issues:
        raise HTTPException(
            status_code=400,
            detail=f"Please add missing fields before saving: {'; '.join(validation_issues)}",
        )

    return {
        "saved": {
            "projects": len(created_projects),
            "experiences": len(created_experiences),
            "achievements": len(created_achievements),
            "educations": len(created_educations),
        },
        "items": {
            "projects": created_projects,
            "experiences": created_experiences,
            "achievements": created_achievements,
            "educations": created_educations,
        },
    }
