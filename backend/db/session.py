from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, create_engine
from sqlalchemy.engine import Engine


_engine: Engine | None = None


class DatabaseConfigurationError(RuntimeError):
    pass


def configure_database(*, use_sqlite: bool, sqlite_db_path: str, database_url: str | None) -> Engine:
    global _engine

    if use_sqlite:
        url = f"sqlite:///{sqlite_db_path}"
        _engine = create_engine(url, echo=False, connect_args={"check_same_thread": False})
        return _engine

    if not database_url or not database_url.strip():
        raise DatabaseConfigurationError("DATABASE_URL is required when USE_SQLITE is false")

    _engine = create_engine(database_url.strip(), echo=False)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise DatabaseConfigurationError("Database engine is not configured")
    return _engine


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
