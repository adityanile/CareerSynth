from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from api.utils import model_to_partial_dict
from core.auth import authorize_and_get_oid, requires_auth
from domain.models import AchievementCreate, AchievementPatch
from domain.repository import (
    ProfileNotFoundError,
    ProfileValidationError,
    create_achievement_for_user,
    delete_achievement_for_user,
    get_achievement_for_user,
    list_achievements_for_user,
    update_achievement_for_user,
)


router = APIRouter()


@router.get("/api/achievements")
@requires_auth
async def list_achievements(
    request: Request,
    organisation: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    items = list_achievements_for_user(oid=oid, organisation=organisation, name=name)
    return {"items": items}


@router.post("/api/achievements", status_code=201)
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


@router.get("/api/achievements/{achievement_id}")
@requires_auth
async def get_achievement(request: Request, achievement_id: int) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    try:
        return get_achievement_for_user(oid=oid, achievement_id=achievement_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/achievements/by-organisation/{organisation}")
@requires_auth
async def get_achievements_by_organisation(request: Request, organisation: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    organisation_value = organisation.strip()
    if not organisation_value:
        raise HTTPException(status_code=400, detail="organisation is required")
    items = list_achievements_for_user(oid=oid, organisation=organisation_value)
    return {"items": items}


@router.get("/api/achievements/by-name/{name}")
@requires_auth
async def get_achievements_by_name(request: Request, name: str) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    name_value = name.strip()
    if not name_value:
        raise HTTPException(status_code=400, detail="name is required")
    items = list_achievements_for_user(oid=oid, name=name_value)
    return {"items": items}


@router.patch("/api/achievements/{achievement_id}")
@requires_auth
async def patch_achievement(
    request: Request,
    achievement_id: int,
    payload: AchievementPatch,
) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    updates = model_to_partial_dict(payload)
    try:
        return update_achievement_for_user(oid=oid, achievement_id=achievement_id, updates=updates)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/achievements/{achievement_id}", status_code=204)
@requires_auth
async def delete_achievement(request: Request, achievement_id: int) -> None:
    oid = authorize_and_get_oid(request)
    try:
        delete_achievement_for_user(oid=oid, achievement_id=achievement_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
