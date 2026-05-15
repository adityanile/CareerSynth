from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def install_jwt_openapi_security(app_instance: FastAPI) -> None:
    def custom_openapi():
        if app_instance.openapi_schema:
            return app_instance.openapi_schema

        schema = get_openapi(
            title=app_instance.title,
            version="1.0.0",
            description=(
                "CareerSynth backend APIs.\n\n"
                "JWT Bearer authentication is required for all `/api/*`, `/auth/test`, and AG-UI routes."
            ),
            routes=app_instance.routes,
        )

        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste access token as: Bearer <JWT>",
        }

        for path, operations in schema.get("paths", {}).items():
            if path == "/health":
                continue
            if not isinstance(operations, dict):
                continue
            for operation in operations.values():
                if isinstance(operation, dict):
                    operation["security"] = [{"BearerAuth": []}]

        app_instance.openapi_schema = schema
        return app_instance.openapi_schema

    app_instance.openapi = custom_openapi

