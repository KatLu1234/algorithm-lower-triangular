from typing import Any
from fastapi import APIRouter

router = APIRouter()

@router.get("/health-check", status_code=200)
def health_check() -> Any:
    """
    Health check endpoint.
    """
    return {"status": "ok"}
