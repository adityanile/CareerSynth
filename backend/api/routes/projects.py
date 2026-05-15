from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from api.utils import model_to_partial_dict
from core.auth import authorize_and_get_oid, requires_auth
from domain.models import ProjectCreate, ProjectPatch
from domain.repository import (
    ProjectNotFoundError,
    ProjectValidationError,
    create_project_for_user,
    delete_project_for_user,
    get_project_for_user,
    get_projects_by_tag_for_user,
    list_projects_for_user,
    update_project_for_user,
)


router = APIRouter()


@router.get("/api/projects")
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


@router.post("/api/projects", status_code=201)
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


@router.get("/api/projects/{project_id}")
@requires_auth
async def get_project(request: Request, project_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return get_project_for_user(oid=oid, project_id=project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/projects/by-tag/{tag}")
@requires_auth
async def get_projects_by_tag(request: Request, tag: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        items = get_projects_by_tag_for_user(oid=oid, tag=tag)
        return {"items": items}
    except ProjectValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/projects/by-tech/{tech}")
@requires_auth
async def get_projects_by_tech(request: Request, tech: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    tech_value = tech.strip()
    if not tech_value:
        raise HTTPException(status_code=400, detail="tech is required")
    items = list_projects_for_user(oid=oid, tech=tech_value)
    return {"items": items}


@router.patch("/api/projects/{project_id}")
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


@router.delete("/api/projects/{project_id}", status_code=204)
@requires_auth
async def delete_project(request: Request, project_id: int) -> None:
    oid = authorize_and_get_oid(request)
    try:
        delete_project_for_user(oid=oid, project_id=project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
