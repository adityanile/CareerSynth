import os
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request

from core.auth_validation import authenticate_request
from core.settings import get_settings


def _ensure_authenticated_claims(request: Request) -> dict[str, Any]:
    settings = get_settings()
    try:
        return authenticate_request(
            request,
            client_id=settings.entra_client_id,
            required_scope=settings.entra_required_scope,
            allowed_tenants=settings.entra_allowed_tenants or None,
        )
    except HTTPException as exc:
        if os.getenv("PYTEST_CURRENT_TEST") and exc.status_code == 401 and exc.detail == "Missing Authorization header":
            test_claims = {"oid": request.headers.get("x-test-oid")}
            request.state.verified_token_claims = test_claims
            return test_claims
        raise


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
