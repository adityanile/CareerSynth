from __future__ import annotations

from sqlmodel import SQLModel

from core.settings import Settings
from db.session import configure_database, get_engine

# Ensure SQLModel metadata has all tables registered.
from db import models as _models  # noqa: F401


def init_db() -> None:
    SQLModel.metadata.create_all(get_engine())


def startup_db(settings: Settings) -> None:
    configure_database(
        use_sqlite=settings.use_sqlite,
        sqlite_db_path=settings.sqlite_db_path,
        database_url=settings.database_url,
    )
    if settings.use_sqlite:
        init_db()
