"""Markdown pass — ``markdown-it-py`` tokens → DocTree nodes.

This is the structural core of the parser. It runs on text that has already
been through :mod:`code_guard` (fenced/inline code replaced by sentinels) and
:mod:`equations` (math replaced by sentinels). Those sentinels survive through
markdown-it as plain ``text`` tokens and are spliced back into real nodes by
:mod:`pipeline` after this pass — so this code only deals with markdown
structure, not with code/equation contents.

Design: a single recursive :class:`TokenStream` cursor walks the flat token
list. Block containers (list, blockquote, table, list_item) recurse by
consuming tokens until their matching ``*_close``.
"""

from __future__ import annotations

import re
from typing import Iterator

from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.models import (
    BlockQuote,
    CodeBlock,
    Heading,
    Image,
    InlineEquation,
    ListBlock,
    ListItem,
    Paragraph,
    Run,
    Table,
    TableCell,
    TableRow,
    ThematicBreak,
)
from app.parser.code_guard import SENTINEL_PREFIX, SENTINEL_SUFFIX, sentinel_index

# Task-list marker at the start of a list item's text: ``[ ]`` or ``[x]``.
_TASK_RE = re.compile(r"^\s*\[(?P<check>[ xX])\]\s+(?P<rest>.*)$", re.DOTALL)

# Cell alignment comes through as ``style="text-align:center"``.
_ALIGN_RE = re.compile(r"text-align:\s*(?P<a>left|center|right)", re.IGNORECASE)

# Standalone image: a paragraph whose inline token tree is exactly one image.
# (markdown-it nests the alt-text as children of the image token.)


def _make_md() -> MarkdownIt:
    """Build the markdown-it parser with the rules we need.

    ``linkify`` (autolinking bare URLs like ``example.com``) is OFF because it
    needs the optional ``linkify-it-py`` dependency. Standard Markdown links
    (``[text](url)``) work without it, so we keep the dep list minimal.
    """
    md = MarkdownIt("commonmark", {"html": False, "linkify": False})
    md.enable("table")
    md.enable("strikethrough")
    return md


_MD = _make_md()


def parse_markdown(text: str) -> list:
    """Parse masked markdown text into a list of block DocTree nodes."""
    tokens = _MD.parse(text, {})
    stream = TokenStream(tokens)
    return list(stream.consume_blocks())


# ---------------------------------------------------------------------------
# Token stream cursor
# ---------------------------------------------------------------------------


class TokenStream:
    """Flat-index cursor over a markdown-it token list.

    Each ``consume_*`` method advances :attr:`i` past the tokens it consumed
    and returns the built DocTree node(s). Block-container methods recurse
    until they hit their matching ``*_close`` token.
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    @property
    def cur(self) -> Token | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def peek(self) -> Token | None:
        return self.cur

    def advance(self) -> Token:
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    # --- block dispatch ---------------------------------------------------

    def consume_blocks(self, until: str | None = None) -> Iterator:
        """Yield block nodes until ``until`` close-tag (or end of stream).

        ``until`` is the close-token type that ends this container (e.g.
        ``list_item_close``). When ``None``, consume until end of stream.
        """
        while self.i < len(self.tokens):
            tok = self.tokens[self.i]
            if until and tok.type == until:
                return
            node = self._dispatch_block()
            if node is not None:
                yield node

    def _dispatch_block(self):
        """Consume one block token (and any nested tokens) → node or None."""
        tok = self.advance()
        handler = {
            "heading_open": self._heading,
            "paragraph_open": self._paragraph,
            "fence": self._fence,
            "code_block": self._indented_code,
            "bullet_list_open": self._list_factory(False),
            "ordered_list_open": self._list_factory(True),
            "blockquote_open": self._blockquote,
            "table_open": self._table,
            "hr": self._hr,
            "html_block": self._html_block,
        }.get(tok.type)
        if handler is None:
            # Unknown / unhandled open-close pair: skip to its match to stay
            # aligned (rather than emitting nothing and corrupting nesting).
            if tok.type.endswith("_open"):
                self._skip_to_close(tok.type)
            return None
        return handler(tok)

    # --- individual block handlers ---------------------------------------

    def _heading(self, open_tok: Token) -> Heading:
        # tag is 'h1'..'h6'
        level = int(open_tok.tag[1:])
        inline = self.advance()  # the 'inline' token
        self.advance()  # heading_close
        text = _flatten_text(inline)
        return Heading(level=level, text=text)

    def _paragraph(self, open_tok: Token) -> Paragraph | Image:
        inline = self.advance()
        self.advance()  # paragraph_close
        # Standalone image? inline.children == [image] (image holds alt-text kids).
        if inline.children and len(inline.children) == 1 and inline.children[0].type == "image":
            img = _image_from_token(inline.children[0])
            if img is not None:
                return img
        return Paragraph.model_construct(inline=_inline_children_to_runs(inline.children or []))

    def _fence(self, tok: Token) -> CodeBlock:
        # We normally guard fenced code before markdown runs, but if any slip
        # through (e.g. unusual fence chars) handle them here too.
        return CodeBlock(code=tok.content, lang=(tok.info.strip() or None))

    def _indented_code(self, tok: Token) -> CodeBlock:
        return CodeBlock(code=tok.content, lang=None, show_line_numbers=False)

    def _list_factory(self, ordered: bool):
        def _list(open_tok: Token):
            # Determine effective depth from token level: lists at level 0 are
            # depth 1, nested lists deeper. We map level//2 + 1, clamped 1..6.
            depth = max(1, min(6, open_tok.level // 2 + 1))
            items: list[ListItem] = []
            while self.i < len(self.tokens):
                tok = self.tokens[self.i]
                if tok.type == "bullet_list_close" or tok.type == "ordered_list_close":
                    self.advance()  # consume close
                    break
                if tok.type == "list_item_open":
                    self.advance()
                    items.append(self._list_item())
                else:
                    self.advance()  # safety: skip stray token
            return ListBlock(ordered=ordered, depth=depth, items=items)

        return _list

    def _list_item(self) -> ListItem:
        """Consume a list item's contents until ``list_item_close``."""
        # The item's "own" text line is its first inline/paragraph; subsequent
        # blocks (nested lists, extra paragraphs) become children.
        item_inline: list = []
        checked: bool | None = None
        children: list = []

        while self.i < len(self.tokens):
            tok = self.tokens[self.i]
            if tok.type == "list_item_close":
                self.advance()
                break
            if tok.type == "paragraph_open":
                inline = self.tokens[self.i + 1]
                self.i += 3  # paragraph_open, inline, paragraph_close
                if not item_inline and not children:
                    # First paragraph → item's main inline line.
                    runs = _inline_children_to_runs(inline.children or [])
                    runs, checked = _extract_task_marker(runs)
                    item_inline = runs
                else:
                    children.append(Paragraph.model_construct(inline=_inline_children_to_runs(inline.children or [])))
            elif tok.type.endswith("_open") and tok.type != "list_item_open":
                node = self._dispatch_block()
                if node is not None:
                    children.append(node)
            else:
                self.advance()  # skip tokens we don't model (blank lines, etc.)

        return ListItem.model_construct(inline=item_inline, checked=checked, children=children)

    def _blockquote(self, open_tok: Token) -> BlockQuote:
        children = list(self.consume_blocks(until="blockquote_close"))
        # consume_blocks returns when it sees the close tag without advancing
        # past it — do that now.
        if self.cur and self.cur.type == "blockquote_close":
            self.advance()
        return BlockQuote(children=children)

    def _table(self, open_tok: Token) -> Table:
        rows: list[TableRow] = []
        cur_cells: list[TableCell] = []
        in_header = False

        while self.i < len(self.tokens):
            tok = self.tokens[self.i]
            if tok.type == "table_close":
                self.advance()
                break
            if tok.type == "thead_open":
                in_header = True
                self.advance()
            elif tok.type == "thead_close":
                in_header = False
                self.advance()
            elif tok.type == "tbody_open" or tok.type == "tbody_close":
                self.advance()
            elif tok.type == "tr_open":
                self.advance()
                cur_cells = []
            elif tok.type == "tr_close":
                self.advance()
                rows.append(TableRow(cells=cur_cells))
                cur_cells = []
            elif tok.type in ("th_open", "td_open"):
                align = _align_from_attrs(tok.attrs)
                is_header = tok.type == "th_open" or in_header
                self.advance()  # open
                inline = self.advance()  # inline
                self.advance()  # close (th_close/td_close)
                cur_cells.append(
                    TableCell.model_construct(
                        inline=_inline_children_to_runs(inline.children or []),
                        align=align,
                        is_header=is_header,
                    )
                )
            else:
                self.advance()

        return Table(rows=rows)

    def _hr(self, tok: Token) -> ThematicBreak:
        return ThematicBreak()

    def _html_block(self, tok: Token) -> Paragraph | None:
        # We render HTML as a plain code-ish paragraph (no raw HTML in .docx).
        text = tok.content.strip()
        if not text:
            return None
        return Paragraph.model_construct(inline=[Run(text=text, code=True)])

    # --- helpers ---------------------------------------------------------

    def _skip_to_close(self, open_type: str) -> None:
        """Advance past everything until the close matching ``open_type``."""
        close_type = open_type.replace("_open", "_close")
        depth = 1
        while self.i < len(self.tokens) and depth > 0:
            t = self.tokens[self.i]
            if t.type == open_type:
                depth += 1
            elif t.type == close_type:
                depth -= 1
            self.i += 1


# ---------------------------------------------------------------------------
# Inline handling
# ---------------------------------------------------------------------------


def _inline_children_to_runs(children: list[Token]) -> list:
    """Convert inline markdown-it tokens to DocTree inline nodes.

    Emits :class:`Run`, :class:`Hyperlink`, :class:`InlineEquation`, and (for
    inline images) :class:`Image` nodes. Tracks an emphasis stack so nested
    bold/italic/code combine correctly.
    """
    out: list = []
    bold = italic = strike = code = False
    link_url: str | None = None
    link_buf: list[str] = []  # accumulate text inside a link

    def _emit_text(text: str) -> None:
        """Append ``text`` (or split it around a sentinel) to ``out``."""
        if link_url is not None:
            link_buf.append(text)
            return
        out.extend(_make_runs_or_sentinels(text, bold, italic, strike, code))

    for tok in children:
        if tok.type == "text":
            _emit_text(tok.content)
        elif tok.type == "code_inline":
            # Inline code always wins over current emphasis.
            if link_url is not None:
                link_buf.append(tok.content)
            else:
                out.append(Run(text=tok.content, code=True))
        elif tok.type == "strong_open":
            bold = True
        elif tok.type == "strong_close":
            bold = False
        elif tok.type == "em_open":
            italic = True
        elif tok.type == "em_close":
            italic = False
        elif tok.type == "s_open":
            strike = True
        elif tok.type == "s_close":
            strike = False
        elif tok.type == "link_open":
            link_url = dict(tok.attrs).get("href", "")
            link_buf = []
        elif tok.type == "link_close":
            from app.models import Hyperlink

            out.append(Hyperlink(text="".join(link_buf), url=link_url or ""))
            link_url = None
            link_buf = []
        elif tok.type == "image":
            # Inline image inside a paragraph (rare; treat as embedded node).
            img = _image_from_token(tok)
            if img is not None:
                out.append(img)
        elif tok.type == "softbreak" or tok.type == "hardbreak":
            _emit_text(" ")
        # Ignore unknown inline tokens (entity, etc.) — markdown-it pre-resolves
        # entities into text, so we usually won't see them.

    # Drop empty runs for cleanliness.
    return [
        r
        for r in out
        if not (
            isinstance(r, Run)
            and r.text == ""
            and not any([r.bold, r.italic, r.strike, r.code])
        )
    ]


def _make_runs_or_sentinels(text: str, bold: bool, italic: bool, strike: bool, code: bool) -> list:
    """Build inline nodes from a text fragment, splitting on any sentinels.

    A sentinel may appear anywhere in ``text`` (whole-text, leading, trailing,
    or mid-text, possibly multiple). Surrounding text becomes ordinary Runs;
    each sentinel becomes an opaque :class:`_SentinelRef` for the pipeline to
    resolve. Always returns a flat list.
    """
    if SENTINEL_PREFIX not in text:
        return [Run(text=text, bold=bold, italic=italic, strike=strike, code=code)]

    out: list = []
    cursor = 0
    while cursor < len(text):
        start = text.find(SENTINEL_PREFIX, cursor)
        if start == -1:
            out.append(
                Run(
                    text=text[cursor:],
                    bold=bold,
                    italic=italic,
                    strike=strike,
                    code=code,
                )
            )
            break
        # Search for the CLOSING NUL *after* the prefix (not the opening NUL
        # that is part of the prefix itself).
        after_prefix = start + len(SENTINEL_PREFIX)
        end = text.find(SENTINEL_SUFFIX, after_prefix)
        if end == -1:
            # Malformed (no closing NUL) — treat the rest as literal text.
            out.append(
                Run(
                    text=text[cursor:],
                    bold=bold,
                    italic=italic,
                    strike=strike,
                    code=code,
                )
            )
            break
        if start > cursor:
            out.append(
                Run(
                    text=text[cursor:start],
                    bold=bold,
                    italic=italic,
                    strike=strike,
                    code=code,
                )
            )
        sentinel = text[start : end + len(SENTINEL_SUFFIX)]
        idx = sentinel_index(sentinel)
        if idx is not None:
            out.append(_SentinelRef(idx=idx, raw=sentinel))
        cursor = end + len(SENTINEL_SUFFIX)
    return out


class _SentinelRef:
    """Opaque placeholder for a code/equation slot, resolved by the pipeline.

    Stored as a plain object (not a pydantic model) so it can never leak into
    the serialized DocTree — :func:`pipeline.resolve_sentinels` replaces every
    occurrence with the real node before returning.
    """

    __slots__ = ("idx", "raw")

    def __init__(self, idx: int, raw: str = ""):
        self.idx = idx
        self.raw = raw


def _flatten_text(inline_tok: Token) -> str:
    """Concatenate all text content from an ``inline`` token's children."""
    if not inline_tok.children:
        return ""
    return "".join(t.content for t in inline_tok.children if t.type in ("text", "code_inline"))


def _align_from_attrs(attrs) -> str:
    """Extract ``left|center|right`` from a cell's style attribute.

    markdown-it-py 3.x stores ``attrs`` as a plain dict; we also tolerate the
    legacy list-of-tuples shape defensively.
    """
    if not attrs:
        return "left"
    style = None
    if isinstance(attrs, dict):
        style = attrs.get("style")
    else:
        for k, v in attrs:
            if k == "style":
                style = v
                break
    if style:
        m = _ALIGN_RE.search(style)
        if m:
            return m.group("a").lower()
    return "left"


def _image_from_token(tok: Token) -> Image | None:
    """Build an :class:`Image` from a markdown-it ``image`` token."""
    attrs = dict(tok.attrs)
    src = attrs.get("src", "")
    if not src:
        return None
    alt = attrs.get("alt", "")
    # Alt text is also nested as children text — prefer attrs, fall back.
    if not alt and tok.children:
        alt = "".join(c.content for c in tok.children if c.type == "text")
    if src.startswith("data:"):
        # data:image/png;base64,XXXX  → split mime / payload
        mime, _, payload = src[5:].partition(",")
        mime = mime.split(";")[0] or "image/png"
        return Image(base64=payload, alt=alt, mime=mime)
    return Image(url=src, alt=alt)


def _extract_task_marker(runs: list):
    """If the first run(s) form ``[ ]``/``[x]``, strip it and return checked state."""
    if not runs:
        return runs, None
    first = runs[0]
    if not isinstance(first, Run) or not isinstance(first.text, str):
        return runs, None
    m = _TASK_RE.match(first.text)
    if not m:
        return runs, None
    rest = m.group("rest")
    checked = m.group("check").lower() == "x"
    new_first = Run(text=rest)
    new_runs = [new_first] + runs[1:]
    return new_runs, checked
