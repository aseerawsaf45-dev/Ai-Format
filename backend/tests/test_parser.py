"""Parser tests.

Run from ``backend/`` with::

    python -m pytest tests/test_parser.py -v

Each test pins one element type so failures point at the offending pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the backend package importable when running pytest from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parser.pipeline import parse_content  # noqa: E402


def _types(doc) -> list[str]:
    """Collect the ``type`` of every top-level child for quick assertions."""
    return [getattr(c, "type", "?") for c in doc.children]


def test_empty_input_returns_empty_doc():
    res = parse_content("")
    assert res.document.children == []
    assert res.stats == {}


def test_headings_levels():
    res = parse_content("# H1\n\n## H2\n\n### H3\n\n###### H6")
    levels = [c.level for c in res.document.children if c.type == "heading"]
    assert levels == [1, 2, 3, 6]
    assert res.stats["heading"] == 4


def test_paragraph_with_inline_formatting():
    res = parse_content("A **bold** and *italic* and `code` line.")
    p = res.document.children[0]
    assert p.type == "paragraph"
    kinds = [(type(n).__name__, getattr(n, "bold", False), getattr(n, "italic", False), getattr(n, "code", False)) for n in p.inline]
    # There must be a bold Run, an italic Run, and a code Run.
    assert any(k[1] for k in kinds), f"no bold run: {kinds}"
    assert any(k[2] for k in kinds), f"no italic run: {kinds}"
    assert any(k[3] for k in kinds), f"no code run: {kinds}"


def test_hyperlink_preserved():
    res = parse_content("See [the docs](https://example.com/docs) now.")
    p = res.document.children[0]
    links = [n for n in p.inline if n.type == "link"]
    assert len(links) == 1
    assert links[0].url == "https://example.com/docs"
    assert links[0].text == "the docs"


def test_inline_equation_converted_to_omml():
    res = parse_content("The formula $a^2 + b^2 = c^2$ is classic.")
    p = res.document.children[0]
    eqs = [n for n in p.inline if n.type == "inline_equation"]
    assert len(eqs) == 1
    assert eqs[0].latex.strip() == "a^2 + b^2 = c^2"
    assert eqs[0].omml is not None and "<m:oMath" in eqs[0].omml


def test_display_equation_becomes_block_node():
    res = parse_content("Intro.\n\n$$E = mc^2$$\n\nOutro.")
    eqs = [c for c in res.document.children if c.type == "block_equation"]
    assert len(eqs) == 1
    assert "<m:oMath" in eqs[0].omml
    assert eqs[0].omml.lstrip().startswith("<m:oMathPara"), eqs[0].omml[:80]


def test_code_fence_with_dollar_not_treated_as_equation():
    src = "```bash\necho $HOME\n```\n"
    res = parse_content(src)
    codes = [c for c in res.document.children if c.type == "code_block"]
    assert len(codes) == 1
    assert "$HOME" in codes[0].code
    # No equation should have been extracted from inside the fence.
    assert res.stats.get("inline_equation", 0) == 0
    assert res.stats.get("block_equation", 0) == 0


def test_inline_code_with_dollar_not_equation():
    res = parse_content("Use `x = $2` literally.")
    p = res.document.children[0]
    runs = [n for n in p.inline if n.type == "run" and n.code]
    assert runs and "$2" in runs[0].text
    assert res.stats.get("inline_equation", 0) == 0


def test_unordered_list_with_nesting_and_tasks():
    res = parse_content("- a\n- b\n  - nested\n- [ ] todo\n- [x] done")
    lists = [c for c in res.document.children if c.type == "list"]
    assert len(lists) == 1
    top = lists[0]
    assert top.ordered is False
    assert len(top.items) == 4
    # item[1].children should contain a nested ListBlock.
    assert any(c.type == "list" for c in top.items[1].children)
    # Task items carry checked state.
    checked_states = [it.checked for it in top.items]
    assert checked_states[2] is False  # [ ]
    assert checked_states[3] is True   # [x]


def test_ordered_list():
    res = parse_content("1. first\n2. second\n3. third")
    lists = [c for c in res.document.children if c.type == "list"]
    assert len(lists) == 1 and lists[0].ordered is True
    assert len(lists[0].items) == 3


def test_table_with_alignment_and_header():
    res = parse_content(
        "| L | C | R |\n"
        "|:--|:-:|--:|\n"
        "| a | b | c |\n"
    )
    tables = [c for c in res.document.children if c.type == "table"]
    assert len(tables) == 1
    t = tables[0]
    assert len(t.rows) == 2
    header = t.rows[0]
    assert all(cell.is_header for cell in header.cells)
    aligns = [cell.align for cell in t.rows[1].cells]
    assert aligns == ["left", "center", "right"]


def test_blockquote_with_inner_paragraph():
    res = parse_content("> quoted text here")
    quotes = [c for c in res.document.children if c.type == "blockquote"]
    assert len(quotes) == 1
    inner = quotes[0].children
    assert any(c.type == "paragraph" for c in inner)


def test_standalone_image():
    res = parse_content("![alt text](https://example.com/x.png)")
    imgs = [c for c in res.document.children if c.type == "image"]
    assert len(imgs) == 1
    assert imgs[0].url == "https://example.com/x.png"
    assert imgs[0].alt == "alt text"


def test_base64_image():
    res = parse_content("![x](data:image/png;base64,iVBORw0KGgo=)")
    imgs = [c for c in res.document.children if c.type == "image"]
    assert len(imgs) == 1
    assert imgs[0].base64 == "iVBORw0KGgo="
    assert imgs[0].mime == "image/png"


def test_thematic_break():
    res = parse_content("above\n\n---\n\nbelow")
    hrs = [c for c in res.document.children if c.type == "thematic_break"]
    assert len(hrs) == 1


def test_sample_fixture_parses_without_error():
    """End-to-end: the bundled sample.md must parse cleanly."""
    sample = Path(__file__).parent / "fixtures" / "sample.md"
    res = parse_content(sample.read_text(encoding="utf-8"))
    types_present = set(_types(res.document))
    # Expect a healthy mix of node types.
    assert "heading" in types_present
    assert "table" in types_present
    assert "code_block" in types_present
    assert "list" in types_present
    assert "blockquote" in types_present
    assert "image" in types_present
    assert "block_equation" in types_present
    assert "thematic_break" in types_present
    assert res.stats.get("inline_equation", 0) >= 1
