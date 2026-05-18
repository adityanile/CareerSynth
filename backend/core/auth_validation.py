from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request
from clerk_backend_api.security import authenticate_request as clerk_authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions


def _is_test_bypass(request: Request) -> bool:
    return bool(os.getenv("PYTEST_CURRENT_TEST")) and bool(request.headers.get("x-test-oid"))


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization header must be Bearer <token>")
    return parts[1]


def authenticate_request(
    request: Request,
    *,
    secret_key: str,
    audience: str | list[str] | None = None,
    authorized_parties: list[str] | None = None,
    jwt_key: str | None = None,
) -> dict[str, Any]:
    existing_claims = getattr(request.state, "verified_token_claims", None)
    if isinstance(existing_claims, dict):
        return existing_claims

    if _is_test_bypass(request):
        test_claims = {"oid": request.headers.get("x-test-oid")}
        request.state.verified_token_claims = test_claims
        return test_claims

    _extract_bearer_token(request)

    request_state = clerk_authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=secret_key,
            jwt_key=jwt_key,
            audience=audience,
            authorized_parties=authorized_parties,
        ),
    )
    if not request_state.is_signed_in or not isinstance(request_state.payload, dict):
        detail = request_state.message or "Unable to parse authentication"
        raise HTTPException(status_code=401, detail=f"Token error: {detail}")

    decoded = dict(request_state.payload)
    request.state.verified_token_claims = decoded
    return decoded
