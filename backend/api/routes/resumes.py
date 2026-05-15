import os
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query, Request
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

from api.utils import model_to_partial_dict
from core.auth import authorize_and_get_oid, requires_auth
from domain.models import ResumeCreate, ResumePatch
from domain.repository import (
    ProfileNotFoundError,
    ProfileValidationError,
    create_resume_for_user,
    delete_resume_for_user,
    get_resume_for_user,
    list_resumes_for_user,
    update_resume_for_user,
)


router = APIRouter()


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
