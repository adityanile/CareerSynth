from typing import Any

from fastapi import APIRouter, Request

from core.auth import authorize_and_get_oid, requires_auth


router = APIRouter()


@router.get("/auth/test")
@requires_auth
async def auth_test(request: Request) -> dict[str, Any]:
    oid = authorize_and_get_oid(request)
    return {"message": "You are authenticated", "oid": oid}

