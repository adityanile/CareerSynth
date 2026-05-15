import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv
from fastapi_microsoft_identity import initialize


load_dotenv()


@dataclass(frozen=True)
class Settings:
    entra_tenant_id: str
    entra_client_id: str
    entra_required_scope: str
    entra_allowed_tenants: list[str]
    sqlite_db_path: str
    azure_openai_deployment: str | None
    azure_openai_endpoint: str | None
    azure_openai_api_key: str | None
    mem0_api_key: str | None
    mem0_application_id: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    entra_tenant_id = os.getenv("ENTRA_TENANT_ID")
    entra_client_id = os.getenv("ENTRA_CLIENT_ID")
    if not entra_tenant_id or not entra_client_id:
        raise RuntimeError("ENTRA_TENANT_ID and ENTRA_CLIENT_ID are required.")

    initialize(tenant_id_=entra_tenant_id, client_id_=entra_client_id)

    raw_allowed_tenants = os.getenv("ENTRA_ALLOWED_TENANTS", "")
    allowed_tenants = [tenant.strip() for tenant in raw_allowed_tenants.split(",") if tenant.strip()]

    return Settings(
        entra_tenant_id=entra_tenant_id,
        entra_client_id=entra_client_id,
        entra_required_scope=os.getenv("ENTRA_REQUIRED_SCOPE", "User"),
        entra_allowed_tenants=allowed_tenants,
        sqlite_db_path=os.getenv("SQLITE_DB_PATH", "careersynth.db"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        mem0_api_key=os.getenv("MEM0_API_KEY"),
        mem0_application_id=os.getenv("MEM0_APPLICATION_ID", "careersynth-main-agent"),
    )
