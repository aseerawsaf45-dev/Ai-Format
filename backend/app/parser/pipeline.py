"""Parser pipeline — orchestrates the deterministic passes.

Order matters:

1. :func:`code_guard.protect_code` — fenced + inline code → sentinels.
   (Keeps ``$``/``*`` inside code from being reinterpreted.)
2. :func:`protect_equations` — ``$...$`` / ``$$...$$`` → sentinels,
   each carrying its cached OMML.
3. :func:`markdown_parser.parse_markdown` — markdown-it tokens → DocTree.
4. :func:`resolve_sentinels` — replace placeholders with the real
   :class:`CodeBlock` / :class:`InlineEquation` / :class:`BlockEquation` nodes.
5. Stats — count node types for the Elements Summary.

Everything is deterministic; no LLM is involved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models import (
    BlockEquation,
    CodeBlock,
    Document,
    InlineEquation,
    ParseResponse,
    Run,
)
from app.parser import equations as eq_mod
from app.parser import markdown_parser as md_parser
from app.parser.code_guard import CodeSlot, protect_code

# Equation sentinels use PUA-delimited markers (never appear in real text).
# ``EQ:`` = display, ``EQI:`` = inline. Capture the index in group 1.
_EQ_SENTINEL_RE = re.compile(r"\uE000EQ(?:I)?:(\d+)\uE000")


# ---------------------------------------------------------------------------
# Equation protection (runs after code guard)
# ---------------------------------------------------------------------------


@dataclass
class _EqSlot:
    """A protected equation. Mirrors :class:`code_guard.CodeSlot`."""

    latex: str
    omml: str | None
    display: bool


_DISPLAY_SENTINEL = "\uE000EQ:"
_INLINE_SENTINEL = "\uE000EQI:"
_SENTINEL_END = "\uE000"


def protect_equations(text: str) -> tuple[str, list[_EqSlot]]:
    """Replace ``$$...$$`` and ``$...$`` with sentinels; return (masked, slots).

    Display math is replaced first so inline ``$`` never eats across a ``$$``.
    Failed conversions are left as their original text (no sentinel) so the
    reader still sees the LaTeX.
    """
    slots: list[_EqSlot] = []

    def _add(latex: str, display: bool, prefix: str) -> str:
        omml = eq_mod._clean_omml(
            eq_mod.latex_to_omml(latex, display=display), display=display
        )
        if omml is None:
            # Conversion failed — keep raw LaTeX so content isn't lost.
            return f"$${latex}$$" if display else f"${latex}$"
        idx = len(slots)
        slots.append(_EqSlot(latex=latex, omml=omml, display=display))
        return f"{prefix}{idx}{_SENTINEL_END}"

    def _display_sub(m: re.Match[str]) -> str:
        return _add(m.group("body").strip(), display=True, prefix=_DISPLAY_SENTINEL)

    def _inline_sub(m: re.Match[str]) -> str:
        return _add(m.group("body").strip(), display=False, prefix=_INLINE_SENTINEL)

    masked = eq_mod._DISPLAY_RE.sub(_display_sub, text)
    masked = eq_mod._INLINE_RE.sub(_inline_sub, masked)
    return masked, slots


def _classify_eq_sentinel(token: str) -> tuple[int, bool] | None:
    """Return ``(slot_index, display?)`` for an equation sentinel, else ``None``."""
    if not token.endswith(_SENTINEL_END):
        return None
    if token.startswith(_DISPLAY_SENTINEL):
        core = token[len(_DISPLAY_SENTINEL) : -len(_SENTINEL_END)]
        try:
            return int(core), True
        except ValueError:
            return None
    if token.startswith(_INLINE_SENTINEL):
        core = token[len(_INLINE_SENTINEL) : -len(_SENTINEL_END)]
        try:
            return int(core), False
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Sentinel resolution
# ---------------------------------------------------------------------------


@dataclass
class _SlotBundle:
    """Holds both code and equation slots, addressable by sentinel index.

    Code-guard indices and equation indices are independent namespaces (they
    use different sentinel prefixes), so we resolve by inspecting the token's
    prefix rather than by a shared index space.
    """

    code_slots: list[CodeSlot] = field(default_factory=list)
    eq_slots: list[_EqSlot] = field(default_factory=list)


def _resolve_inline(node, bundle: _SlotBundle) -> list:
    """Resolve one inline node → a (possibly empty) list of inline nodes.

    Returns a list so equation sentinels embedded mid-Run can split into
    multiple nodes; the caller flattens. Handles:

    * ``_SentinelRef`` (inline code)  → ``Run(code=True)``
    * ``Run`` whose text holds equation sentinels → split into
      ``Run`` + ``InlineEquation`` fragments
    * everything else → unchanged (wrapped in a one-element list)
    """
    # Inline code sentinel from the code guard.
    if isinstance(node, md_parser._SentinelRef):
        if node.idx < len(bundle.code_slots):
            slot = bundle.code_slots[node.idx]
            return [Run(text=slot.code, code=True)]
        return [Run(text=node.raw, code=True)]

    # Equation sentinels arrive as plain text inside a Run.
    if isinstance(node, Run) and isinstance(node.text, str):
        text = node.text
        if _EQ_SENTINEL_RE.search(text) is None:
            return [node]
        out: list = []
        last = 0
        for m in _EQ_SENTINEL_RE.finditer(text):
            if m.start() > last:
                out.append(
                    Run(
                        text=text[last : m.start()],
                        bold=node.bold,
                        italic=node.italic,
                        strike=node.strike,
                        code=node.code,
                    )
                )
            idx = int(m.group(1))
            sentinel = m.group(0)
            display = sentinel.startswith(_DISPLAY_SENTINEL)
            if idx < len(bundle.eq_slots):
                eslot = bundle.eq_slots[idx]
                out.append(InlineEquation(latex=eslot.latex, omml=eslot.omml))
            last = m.end()
        if last < len(text):
            out.append(
                Run(
                    text=text[last:],
                    bold=node.bold,
                    italic=node.italic,
                    strike=node.strike,
                    code=node.code,
                )
            )
        return out

    # Any other inline node (Hyperlink, Image, already-resolved equation…).
    return [node]


def _resolve_inline_list(inlines: list, bundle: _SlotBundle) -> list:
    """Resolve + flatten an inline list."""
    out: list = []
    for n in inlines:
        out.extend(_resolve_inline(n, bundle))
    return out


def _resolve_blocks(blocks: list, bundle: _SlotBundle) -> list:
    """Walk block nodes, resolving sentinels in inline lists.

    Also promotes a paragraph whose only resolved child is an equation into a
    standalone :class:`BlockEquation`.
    """
    resolved: list = []
    for block in blocks:
        btype = getattr(block, "type", None)

        if btype == "paragraph":
            new_inline = _resolve_inline_list(block.inline, bundle)
            # A lone equation (display or inline on its own line) → block math.
            if len(new_inline) == 1 and isinstance(new_inline[0], InlineEquation):
                eq = new_inline[0]
                resolved.append(BlockEquation(latex=eq.latex, omml=eq.omml))
                continue
            resolved.append(block.model_copy(update={"inline": new_inline}))
            continue

        if btype == "list":
            new_items = []
            for item in block.items:
                item_inline = _resolve_inline_list(item.inline, bundle)
                item_children = _resolve_blocks(item.children, bundle)
                new_items.append(
                    item.model_copy(
                        update={"inline": item_inline, "children": item_children}
                    )
                )
            resolved.append(block.model_copy(update={"items": new_items}))
            continue

        if btype == "blockquote":
            resolved.append(
                block.model_copy(
                    update={"children": _resolve_blocks(block.children, bundle)}
                )
            )
            continue

        if btype == "table":
            new_rows = []
            for row in block.rows:
                new_cells = []
                for cell in row.cells:
                    new_cells.append(
                        cell.model_copy(
                            update={
                                "inline": _resolve_inline_list(cell.inline, bundle)
                            }
                        )
                    )
                new_rows.append(row.model_copy(update={"cells": new_cells}))
            resolved.append(block.model_copy(update={"rows": new_rows}))
            continue

        resolved.append(block)
    return resolved


def _splice_fenced_code(blocks: list, bundle: _SlotBundle) -> list:
    """Replace standalone fenced-code sentinel paragraphs with CodeBlock nodes.

    A fenced code block, after the code guard + markdown passes, is a paragraph
    whose only inline child is a ``_SentinelRef`` pointing at a non-inline
    (fenced) code slot. Inline-code sentinels are left in place for
    :func:`_resolve_blocks` to turn into ``Run(code=True)``.
    """
    out: list = []
    for block in blocks:
        if getattr(block, "type", None) != "paragraph" or len(block.inline) != 1:
            out.append(block)
            continue
        only = block.inline[0]
        if (
            isinstance(only, md_parser._SentinelRef)
            and only.idx < len(bundle.code_slots)
            and not bundle.code_slots[only.idx].inline
        ):
            slot = bundle.code_slots[only.idx]
            out.append(
                CodeBlock(
                    code=slot.code, lang=slot.lang, show_line_numbers=False
                )
            )
            continue
        out.append(block)
    return out


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


def parse_content(content: str) -> ParseResponse:
    """Parse AI-generated ``content`` into a DocTree + element stats."""
    if not content or not content.strip():
        return ParseResponse(document=Document(children=[]), stats={})

    # 1. Protect code (fenced + inline).
    masked, code_slots = protect_code(content)

    # 2. Protect equations on the code-masked text.
    masked, eq_slots = protect_equations(masked)

    # 3. Parse markdown structure.
    blocks = md_parser.parse_markdown(masked)

    # 4. Resolve sentinels → real code/equation nodes.
    bundle = _SlotBundle(code_slots=code_slots, eq_slots=eq_slots)
    blocks = _splice_fenced_code(blocks, bundle)
    blocks = _resolve_blocks(blocks, bundle)

    # 5. Build the document + stats.
    doc = Document(children=blocks)
    stats = _compute_stats(doc)
    return ParseResponse(document=doc, stats=stats)


def _compute_stats(doc: Document) -> dict[str, int]:
    """Count block/inline node types for the Elements Summary."""
    counts: dict[str, int] = {}

    def bump(key: str) -> None:
        counts[key] = counts.get(key, 0) + 1

    def walk_blocks(blocks: list) -> None:
        for block in blocks:
            bt = getattr(block, "type", None)
            if bt:
                bump(bt)
            if bt == "list":
                for item in block.items:
                    bump("list_item")
                    walk_inline(item.inline)
                    walk_blocks(item.children)
            elif bt == "blockquote":
                walk_blocks(block.children)
            elif bt == "table":
                for row in block.rows:
                    bump("table_row")
                    for cell in row.cells:
                        walk_inline(cell.inline)
            elif bt == "paragraph":
                walk_inline(block.inline)

    def walk_inline(inlines: list) -> None:
        for node in inlines:
            nt = getattr(node, "type", None)
            if nt:
                bump(nt)

    walk_blocks(doc.children)
    return counts
