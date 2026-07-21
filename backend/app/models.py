"""Typed intermediate representation (DocTree).

The DocTree decouples parsing from rendering:
  AI text → parser → DocTree (JSON) → renderer → .docx
The frontend mirrors these types in ``frontend/lib/types.ts`` for preview.

Every node inherits from :class:`Block` or :class:`Inline`. Adding a new
element type later (e.g. a diagram) is a matter of defining a new model,
handling it in the parser, and adding a renderer case — nothing else changes.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Inline nodes (live inside paragraphs / list items / table cells)
# ---------------------------------------------------------------------------


class Run(BaseModel):
    """A styled text run. Combine flags freely; ``code`` wins for styling."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["run"] = "run"
    text: str
    bold: bool = False
    italic: bool = False
    strike: bool = False
    code: bool = False


class Hyperlink(BaseModel):
    """Clickable link. ``text`` may itself contain markup-free label text."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["link"] = "link"
    text: str
    url: str


class InlineEquation(BaseModel):
    """Inline ``$...$`` equation. ``omml`` is the cached ``<m:oMath>`` XML."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["inline_equation"] = "inline_equation"
    latex: str
    omml: str | None = None


Inline = Annotated[
    Union[Run, Hyperlink, InlineEquation],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Block nodes (direct children of Document or nested containers)
# ---------------------------------------------------------------------------


class Heading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["heading"] = "heading"
    level: int = Field(ge=1, le=6)
    text: str
    # Optional anchor id for future cross-references / TOC.
    id: str | None = None


class Paragraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["paragraph"] = "paragraph"
    inline: list[Inline] = Field(default_factory=list)
    align: Literal["left", "center", "right", "justify"] = "left"


class CodeBlock(BaseModel):
    """Fenced code. ``lang`` drives syntax styling (line numbers, label)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["code_block"] = "code_block"
    code: str
    lang: str | None = None
    show_line_numbers: bool = True


class BlockEquation(BaseModel):
    """Display ``$$...$$`` equation. ``omml`` is ``<m:oMathPara>`` XML."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["block_equation"] = "block_equation"
    latex: str
    omml: str | None = None


class BlockQuote(BaseModel):
    """Callout box. Children are parsed recursively (paragraphs, lists…)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["blockquote"] = "blockquote"
    children: list["Block"] = Field(default_factory=list)


class ListItem(BaseModel):
    """One list entry. ``children`` are nested blocks (sub-lists, paras)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["list_item"] = "list_item"
    # Inline content for the item's own text line.
    inline: list[Inline] = Field(default_factory=list)
    # ``None`` = not a task item; True/False = checked state.
    checked: bool | None = None
    children: list["Block"] = Field(default_factory=list)


class ListBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["list"] = "list"
    ordered: bool = False
    # 1-based depth; renderer maps this to Word's nested list styles.
    depth: int = 1
    items: list[ListItem] = Field(default_factory=list)


class TableCell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["table_cell"] = "table_cell"
    inline: list[Inline] = Field(default_factory=list)
    align: Literal["left", "center", "right"] = "left"
    colspan: int = 1
    rowspan: int = 1
    is_header: bool = False


class TableRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["table_row"] = "table_row"
    cells: list[TableCell] = Field(default_factory=list)


class Table(BaseModel):
    """Markdown or ASCII table. First row with ``is_header`` is the header."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["table"] = "table"
    rows: list[TableRow] = Field(default_factory=list)


class Image(BaseModel):
    """Embedded picture. Either ``url`` or ``base64`` (no data: prefix)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["image"] = "image"
    url: str | None = None
    base64: str | None = None
    alt: str = ""
    caption: str | None = None
    # MIME hint for base64 images ("image/png", "image/jpeg"…).
    mime: str = "image/png"


class ThematicBreak(BaseModel):
    """Horizontal rule → Word bottom-border on an empty paragraph."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["thematic_break"] = "thematic_break"


Block = Annotated[
    Union[
        Heading,
        Paragraph,
        CodeBlock,
        BlockEquation,
        BlockQuote,
        ListBlock,
        Table,
        Image,
        ThematicBreak,
    ],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Document root + API envelopes
# ---------------------------------------------------------------------------


class Document(BaseModel):
    """Root of the DocTree."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["document"] = "document"
    title: str | None = None
    children: list[Block] = Field(default_factory=list)


class ParseResponse(BaseModel):
    """Response envelope for ``POST /api/parse``."""

    model_config = ConfigDict(extra="forbid")

    document: Document
    stats: dict[str, int]


class ExportRequest(BaseModel):
    """Request body for ``POST /api/export``."""

    model_config = ConfigDict(extra="forbid")

    document: Document
    theme: Literal["modern", "academic", "corporate", "minimal"] = "modern"


# Resolve forward references (BlockQuote/ListBlock reference ``Block``).
BlockQuote.model_rebuild()
ListItem.model_rebuild()
Document.model_rebuild()
