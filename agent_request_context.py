from contextvars import ContextVar, Token


_CURRENT_OID: ContextVar[str | None] = ContextVar("current_oid", default=None)
_CURRENT_THREAD_ID: ContextVar[str | None] = ContextVar("current_thread_id", default=None)


def set_current_oid(oid: str) -> Token[str | None]:
    return _CURRENT_OID.set(oid)


def reset_current_oid(token: Token[str | None]) -> None:
    _CURRENT_OID.reset(token)


def set_current_thread_id(thread_id: str) -> Token[str | None]:
    return _CURRENT_THREAD_ID.set(thread_id)


def reset_current_thread_id(token: Token[str | None]) -> None:
    _CURRENT_THREAD_ID.reset(token)


def get_current_oid() -> str | None:
    return _CURRENT_OID.get()


def get_current_thread_id() -> str | None:
    return _CURRENT_THREAD_ID.get()


def require_current_oid() -> str:
    oid = get_current_oid()
    if not oid:
        raise RuntimeError("Missing request oid in agent context")
    return oid


def require_current_thread_id() -> str:
    thread_id = get_current_thread_id()
    if not thread_id:
        raise RuntimeError("Missing request thread_id in agent context")
    return thread_id
