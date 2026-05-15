from __future__ import annotations

from app import app, create_app


__all__ = ["app", "create_app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8888, reload=True)
