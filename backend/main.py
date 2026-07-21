"""FastAPI application entrypoint.

Run locally with::

    uvicorn main:app --reload --port 8000

The app is split into route modules under :mod:`app.routes`. CORS is open to
``localhost:3000`` for the Next.js dev server.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import export, health, parse

app = FastAPI(
    title="AI Document Rendering Engine",
    description=(
        "Convert AI-generated content into native, editable Microsoft Word "
        "documents. Parses Markdown/HTML/LaTeX into a semantic DocTree and "
        "renders it to OOXML."
    ),
    version="0.1.0",
)

# Allow the Next.js dev server (and any explicitly listed origin) to call us.
_allowed_origins = os.environ.get(
    "AI_FORMATER_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["meta"])
app.include_router(parse.router, prefix="/api", tags=["parse"])
app.include_router(export.router, prefix="/api", tags=["export"])
