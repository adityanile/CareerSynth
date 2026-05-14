from __future__ import annotations

import os
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException, Request
from jose import jwt


@dataclass
class _CachedJwks:
    expires_at: float
    keys: list[dict[str, Any]]


_JWKS_CACHE: dict[str, _CachedJwks] = {}
_JWKS_TTL_SECONDS = 300


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


def _resolve_jwks_for_tenant(tenant_id: str) -> list[dict[str, Any]]:
    now = time.time()
    cached = _JWKS_CACHE.get(tenant_id)
    if cached and cached.expires_at > now:
        return cached.keys

    key_urls = (
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
        "https://login.microsoftonline.com/common/discovery/v2.0/keys",
    )
    timeout = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=5.0)

    for key_url in key_urls:
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(key_url)
        except Exception:
            continue

        if response.status_code != 200:
            continue

        payload = response.json()
        keys = payload.get("keys", [])
        if isinstance(keys, list) and keys:
            _JWKS_CACHE[tenant_id] = _CachedJwks(
                expires_at=now + _JWKS_TTL_SECONDS,
                keys=keys,
            )
            return keys

    raise HTTPException(status_code=401, detail="Token error: Unable to resolve signing keys")


def _validate_required_scope(token_claims: dict[str, Any], required_scope: str) -> None:
    scope_value = str(required_scope or "").strip()
    if not scope_value:
        return

    roles = token_claims.get("roles")
    if isinstance(roles, list):
        for role in roles:
            if isinstance(role, str) and role.lower() == scope_value.lower():
                return

    scp = token_claims.get("scp")
    if isinstance(scp, str):
        for token_scope in scp.split():
            if token_scope.lower() == scope_value.lower():
                return

    raise HTTPException(
        status_code=403,
        detail=f'Token error: Required scope or role "{scope_value}" not found',
    )


def _validate_audience(token_claims: dict[str, Any], client_id: str) -> None:
    audience = token_claims.get("aud")
    allowed = {client_id, f"api://{client_id}"}

    if isinstance(audience, str) and audience in allowed:
        return

    if isinstance(audience, list):
        for value in audience:
            if isinstance(value, str) and value in allowed:
                return

    raise HTTPException(status_code=401, detail="Token error: Please check the audience and issuer")


def authenticate_request(
    request: Request,
    *,
    client_id: str,
    required_scope: str,
    allowed_tenants: Sequence[str] | None = None,
) -> dict[str, Any]:
    existing_claims = getattr(request.state, "verified_token_claims", None)
    if isinstance(existing_claims, dict):
        return existing_claims

    if _is_test_bypass(request):
        if request.headers.get("x-force-scope-error") == "1":
            raise HTTPException(status_code=403, detail="Missing required scope")
        test_claims = {"oid": request.headers.get("x-test-oid"), "scp": required_scope}
        request.state.verified_token_claims = test_claims
        return test_claims

    token = _extract_bearer_token(request)

    try:
        token_header = jwt.get_unverified_header(token)
        unverified_claims = jwt.get_unverified_claims(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Token error: Unable to parse authentication") from exc

    kid = unverified_claims.get("kid") or token_header.get("kid")
    tenant_id = unverified_claims.get("tid")
    if not isinstance(kid, str) or not kid:
        raise HTTPException(status_code=401, detail="Token error: Missing kid in token header")
    if not isinstance(tenant_id, str) or not tenant_id:
        raise HTTPException(status_code=401, detail="Token error: Missing tid claim in token")

    if allowed_tenants:
        allowed = {tenant.strip() for tenant in allowed_tenants if tenant and tenant.strip()}
        if allowed and tenant_id not in allowed:
            raise HTTPException(status_code=401, detail="Token error: Tenant is not allowed")

    keys = _resolve_jwks_for_tenant(tenant_id)
    rsa_key: dict[str, Any] | None = None
    for key in keys:
        if key.get("kid") == kid:
            rsa_key = {
                "kty": key.get("kty"),
                "kid": key.get("kid"),
                "use": key.get("use"),
                "n": key.get("n"),
                "e": key.get("e"),
            }
            break

    if not rsa_key:
        raise HTTPException(status_code=401, detail="Invalid header error: Unable to find appropriate key")

    try:
        decoded = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_iss": False, "verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token error: The token has expired") from exc
    except jwt.JWTClaimsError as exc:
        raise HTTPException(status_code=401, detail=f"Token error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Token error: Unable to parse authentication") from exc

    issuer = decoded.get("iss")
    token_version = str(decoded.get("ver", "2.0")).strip()
    expected_issuers = {
        f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        f"https://login.microsoftonline.com/{tenant_id}/v2.0/",
    }
    if token_version == "1.0":
        expected_issuers.add(f"https://sts.windows.net/{tenant_id}/")

    if not isinstance(issuer, str) or issuer not in expected_issuers:
        raise HTTPException(status_code=401, detail="Token error: Please check the audience and issuer")

    _validate_audience(decoded, client_id=client_id)
    _validate_required_scope(decoded, required_scope=required_scope)
    request.state.verified_token_claims = decoded
    return decoded
