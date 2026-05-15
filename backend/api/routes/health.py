from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def home() -> dict[str, str]:
    return {"status": "ok"}

