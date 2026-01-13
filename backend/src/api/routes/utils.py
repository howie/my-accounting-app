from typing import Any

from fastapi import APIRouter

from src.core.version import VERSION

router = APIRouter()


@router.get("/health", response_model=dict[str, Any])
async def health_check() -> Any:
    """
    Health check endpoint.
    """
    return {"status": "healthy", "version": VERSION}
