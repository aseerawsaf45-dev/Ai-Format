"""``POST /api/parse`` — AI text → DocTree.

Wires the parser pipeline; full implementation lands in Phase 2. For now it
exposes the endpoint shape so the frontend can integrate against a stable
contract while the parser is built out.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models import ParseResponse
from app.parser.pipeline import parse_content

router = APIRouter()


class ParseRequest(BaseModel):
    """Incoming request: the raw AI-generated text."""

    content: str = Field(..., min_length=1)


@router.post("/parse", response_model=ParseResponse)
def parse(req: ParseRequest) -> ParseResponse:
    """Analyze ``content`` and return its semantic DocTree + element stats."""
    return parse_content(req.content)
