"""``POST /api/export`` — DocTree → .docx bytes.

Wires the renderer; full implementation lands in Phase 3.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.models import ExportRequest
from app.renderer.docx_builder import render_document

router = APIRouter()


@router.post("/export")
def export(req: ExportRequest) -> Response:
    """Render ``document`` to a Word file and stream it back as ``.docx``."""
    docx_bytes = render_document(req.document, theme_name=req.theme)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="document.docx"'},
    )
