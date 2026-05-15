from fastapi import FastAPI

from agents.runtime import register_agui_endpoint
from api.routes.achievements import router as achievements_router
from api.routes.auth import router as auth_router
from api.routes.experiences import router as experiences_router
from api.routes.health import router as health_router
from api.routes.projects import router as projects_router
from core.openapi import install_jwt_openapi_security
from core.settings import get_settings
from db.schema import startup_db


def create_app() -> FastAPI:
    app = FastAPI(title="AG-UI Server")
    install_jwt_openapi_security(app)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(experiences_router)
    app.include_router(achievements_router)

    register_agui_endpoint(app)

    @app.on_event("startup")
    def on_startup() -> None:
        startup_db(get_settings().sqlite_db_path)

    return app


app = create_app()

