from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Import models so metadata is fully registered.
from db import models as _models  # noqa: F401
from dotenv import load_dotenv

load_dotenv()


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _read_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_database_url() -> str:
    use_sqlite = _read_bool(os.getenv("USE_SQLITE"), default=False)
    if use_sqlite:
        sqlite_db_path = os.getenv("SQLITE_DB_PATH", "careersynth.db")
        return f"sqlite:///{sqlite_db_path}"

    database_url = os.getenv("DATABASE_URL")
    if not database_url or not database_url.strip():
        raise RuntimeError("DATABASE_URL is required when USE_SQLITE is false")
    return database_url.strip()


def run_migrations_offline() -> None:
    url = _resolve_database_url()
    context.configure(
        url=url,
        target_metadata=SQLModel.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    config.set_main_option("sqlalchemy.url", _resolve_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=SQLModel.metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
