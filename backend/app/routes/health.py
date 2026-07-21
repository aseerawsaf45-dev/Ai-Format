"""Health endpoint — liveness probe for the frontend / deployment."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Return ``{"status": "ok"}`` when the service is up."""
    return {"status": "ok"}
