import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


def _read_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    clerk_secret_key: str
    clerk_jwt_key: str | None
    clerk_authorized_parties: list[str]
    clerk_audience: list[str]
    use_sqlite: bool
    sqlite_db_path: str
    database_url: str | None
    azure_openai_deployment: str | None
    azure_openai_endpoint: str | None
    azure_openai_api_key: str | None
    mem0_api_key: str | None
    mem0_application_id: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
    if not clerk_secret_key:
        raise RuntimeError("CLERK_SECRET_KEY is required.")

    raw_authorized_parties = os.getenv("CLERK_AUTHORIZED_PARTIES", "")
    clerk_authorized_parties = [party.strip() for party in raw_authorized_parties.split(",") if party.strip()]

    raw_audience = os.getenv("CLERK_AUDIENCE", "")
    clerk_audience = [value.strip() for value in raw_audience.split(",") if value.strip()]

    use_sqlite = _read_bool(os.getenv("USE_SQLITE"), default=False)
    sqlite_db_path = os.getenv("SQLITE_DB_PATH", "careersynth.db")
    database_url = os.getenv("DATABASE_URL")

    if not use_sqlite and not (database_url and database_url.strip()):
        raise RuntimeError("DATABASE_URL is required when USE_SQLITE is false.")

    return Settings(
        clerk_secret_key=clerk_secret_key,
        clerk_jwt_key=os.getenv("CLERK_JWT_KEY"),
        clerk_authorized_parties=clerk_authorized_parties,
        clerk_audience=clerk_audience,
        use_sqlite=use_sqlite,
        sqlite_db_path=sqlite_db_path,
        database_url=database_url,
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        mem0_api_key=os.getenv("MEM0_API_KEY"),
        mem0_application_id=os.getenv("MEM0_APPLICATION_ID", "careersynth-main-agent"),
    )
