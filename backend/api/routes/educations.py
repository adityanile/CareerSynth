from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from api.utils import model_to_partial_dict
from core.auth import authorize_and_get_oid, requires_auth
from domain.models import EducationCreate, EducationPatch
from domain.repository import (
    ProfileNotFoundError,
    ProfileValidationError,
    create_education_for_user,
    delete_education_for_user,
    get_education_for_user,
    list_educations_for_user,
    update_education_for_user,
)


router = APIRouter()


@router.get("/api/educations")
@requires_auth
async def list_educations(
    request: Request,
    degree_name: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    items = list_educations_for_user(oid=oid, degree_name=degree_name, location=location)
    return {"items": items}


@router.post("/api/educations", status_code=201)
@requires_auth
async def create_education(request: Request, payload: EducationCreate) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return create_education_for_user(
            oid=oid,
            degree_name=payload.degreeName,
            location=payload.location,
            start_year=payload.startYear,
            end_year=payload.endYear,
            cgpa_or_percentage=payload.cgpaOrPercentage,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/educations/{education_id}")
@requires_auth
async def get_education(request: Request, education_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return get_education_for_user(oid=oid, education_id=education_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/educations/by-degree/{degree_name}")
@requires_auth
async def get_educations_by_degree(request: Request, degree_name: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    degree_name_value = degree_name.strip()
    if not degree_name_value:
        raise HTTPException(status_code=400, detail="degree_name is required")
    items = list_educations_for_user(oid=oid, degree_name=degree_name_value)
    return {"items": items}


@router.patch("/api/educations/{education_id}")
@requires_auth
async def patch_education(
    request: Request,
    education_id: int,
    payload: EducationPatch,
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    updates = model_to_partial_dict(payload)
    try:
        return update_education_for_user(oid=oid, education_id=education_id, updates=updates)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/educations/{education_id}", status_code=204)
@requires_auth
async def delete_education(request: Request, education_id: int) -> None:
    oid = authorize_and_get_oid(request)
    try:
        delete_education_for_user(oid=oid, education_id=education_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
