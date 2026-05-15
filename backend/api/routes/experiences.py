from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from api.utils import model_to_partial_dict
from core.auth import authorize_and_get_oid, requires_auth
from domain.models import ExperienceCreate, ExperiencePatch
from domain.repository import (
    ProfileNotFoundError,
    ProfileValidationError,
    create_experience_for_user,
    delete_experience_for_user,
    get_experience_for_user,
    list_experiences_for_user,
    update_experience_for_user,
)


router = APIRouter()


@router.get("/api/experiences")
@requires_auth
async def list_experiences(
    request: Request,
    position: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    items = list_experiences_for_user(oid=oid, position=position)
    return {"items": items}


@router.post("/api/experiences", status_code=201)
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


@router.get("/api/experiences/{experience_id}")
@requires_auth
async def get_experience(request: Request, experience_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return get_experience_for_user(oid=oid, experience_id=experience_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/experiences/by-position/{position}")
@requires_auth
async def get_experiences_by_position(request: Request, position: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    position_value = position.strip()
    if not position_value:
        raise HTTPException(status_code=400, detail="position is required")
    items = list_experiences_for_user(oid=oid, position=position_value)
    return {"items": items}


@router.get("/api/experiences/by-company/{company_name}")
@requires_auth
async def get_experiences_by_company(request: Request, company_name: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    company_value = company_name.strip()
    if not company_value:
        raise HTTPException(status_code=400, detail="company_name is required")
    items = list_experiences_for_user(oid=oid, company_name=company_value)
    return {"items": items}


@router.patch("/api/experiences/{experience_id}")
@requires_auth
async def patch_experience(
    request: Request,
    experience_id: int,
    payload: ExperiencePatch,
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    updates = model_to_partial_dict(payload)
    try:
        return update_experience_for_user(oid=oid, experience_id=experience_id, updates=updates)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/experiences/{experience_id}", status_code=204)
@requires_auth
async def delete_experience(request: Request, experience_id: int) -> None:
    oid = authorize_and_get_oid(request)
    try:
        delete_experience_for_user(oid=oid, experience_id=experience_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
