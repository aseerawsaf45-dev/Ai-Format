"""Equation pass — convert ``$...$`` / ``$$...$$`` LaTeX into cached OMML.

This runs AFTER :mod:`code_guard` so equations inside code are never touched.

Pipeline per equation:
    LaTeX source
      → MathML  (via ``latex2mathml.converter.convert``)
      → OMML    (via the bundled ``MML2OMML.XSL`` stylesheet + ``lxml``)

The OMML is cached as a string on the produced :class:`InlineEquation` /
:class:`BlockEquation` node so the renderer can inject it verbatim without
re-running the transform. If conversion fails for a specific equation, we
fall back to a plain run of the LaTeX source (graceful degradation — the
document still renders, just without a native equation object for that one).

Sentinels replace equations so the markdown pass sees plain text where math
used to be; :mod:`pipeline` splices the equation nodes back in at render time.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from lxml import etree

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
XSL_PATH = ASSETS_DIR / "MML2OMML.XSL"

# Match $$...$$ or \[...\] for display math before $...$ or \(...\) for inline.
# Also forgives unescaped [ ... ] if they are on a line by themselves (e.g. pasted from chat).
# Backslash-escaped (\$) is left alone. We use non-greedy matches.
_DISPLAY_RE = re.compile(r"(?:\$\$|\\\[|^[ \t]*\[[ \t]*)(?P<body>.+?)(?:\$\$|\\\]|[ \t]*\][ \t]*$)", re.MULTILINE | re.DOTALL)
_INLINE_RE = re.compile(r"(?:(?<![\\$])\$|\\\()(?P<body>.+?)(?:\$(?!\$)|\\\))")


@lru_cache(maxsize=1)
def _load_transform() -> etree.XSLT:
    """Load and compile the MML→OMML stylesheet once per process."""
    if not XSL_PATH.exists():
        raise FileNotFoundError(
            f"MML2OMML.XSL not found at {XSL_PATH}. "
            "It must be present under backend/assets/ for equation rendering."
        )
    parsed = etree.parse(str(XSL_PATH))
    return etree.XSLT(parsed)


def latex_to_omml(latex: str, display: bool = False) -> str | None:
    """Convert a LaTeX math string to OMML XML text.

    Returns ``None`` on any failure so the caller can degrade gracefully.
    ``display`` only affects the MathML ``display`` attribute, which the XSLT
    largely ignores — wrapping into ``<m:oMathPara>`` for display math is the
    renderer's job.
    """
    try:
        import latex2mathml.converter as _l2m

        # latex2mathml wraps the input in <math>..</math> for us.
        mathml_str = _l2m.convert(latex)
        # Parse to an element tree the XSLT can consume.
        mathml_tree = etree.fromstring(mathml_str)
        transform = _load_transform()
        result_tree = transform(mathml_tree)
        return str(result_tree)
    except Exception:
        # Any failure (bad LaTeX, missing stylesheet, transform error) → None.
        # The caller keeps the raw LaTeX so the content is not lost.
        return None


def _strip_xml_decl(omml: str) -> str:
    """Drop the ``<?xml ...?>`` prologue so the fragment is spliceable."""
    return omml.replace('<?xml version="1.0"?>', "").strip()


def _clean_omml(omml_raw: str | None, display: bool) -> str | None:
    """Normalize an OMML string for storage on a DocTree node."""
    if omml_raw is None:
        return None
    body = _strip_xml_decl(omml_raw)
    if not body:
        return None
    if display:
        # Wrap display math in oMathPara (paragraph-level equation).
        if not body.startswith("<m:oMathPara"):
            body = f"<m:oMathPara xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\">{body}</m:oMathPara>"
    return body
