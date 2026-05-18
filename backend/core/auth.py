from functools import wraps
from typing import Any

from fastapi import HTTPException, Request

from core.auth_validation import authenticate_request
from core.settings import get_settings


def _ensure_authenticated_claims(request: Request) -> dict[str, Any]:
    settings = get_settings()
    return authenticate_request(
        request,
        secret_key=settings.clerk_secret_key,
        audience=settings.clerk_audience or None,
        authorized_parties=settings.clerk_authorized_parties or None,
        jwt_key=settings.clerk_jwt_key,
    )


def requires_auth(route_handler):
    @wraps(route_handler)
    async def decorated(*args, **kwargs):
        request = kwargs.get("request")
        if not isinstance(request, Request):
            raise HTTPException(status_code=500, detail="Request context is required")
        _ensure_authenticated_claims(request)
        return await route_handler(*args, **kwargs)

    return decorated


def get_oid_or_401(request: Request) -> str:
    token_claims = _ensure_authenticated_claims(request)
    oid = token_claims.get("oid")
    if not oid:
        raise HTTPException(status_code=401, detail="Missing oid claim in token")
    return str(oid)


def authorize_and_get_oid(request: Request) -> str:
    _ensure_authenticated_claims(request)
    return get_oid_or_401(request)
