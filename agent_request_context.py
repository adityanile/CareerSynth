from contextvars import ContextVar, Token


_CURRENT_OID: ContextVar[str | None] = ContextVar("current_oid", default=None)


def set_current_oid(oid: str) -> Token[str | None]:
    return _CURRENT_OID.set(oid)


def reset_current_oid(token: Token[str | None]) -> None:
    _CURRENT_OID.reset(token)


def get_current_oid() -> str | None:
    return _CURRENT_OID.get()


def require_current_oid() -> str:
    oid = get_current_oid()
    if not oid:
        raise RuntimeError("Missing request oid in agent context")
    return oid
