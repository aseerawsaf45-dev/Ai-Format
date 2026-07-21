"""Code guard pass — protect fenced code blocks from later reinterpretation.

markdown-it-py already understands fenced code, but we also run equation and
inline-format passes that must NOT touch code contents (a ``$`` in a shell
snippet is not an equation, ``*`` in a C comment is not bold). This module
extracts fenced code blocks up front, replaces them with sentinels, and lets
the caller splice the originals back in afterwards.

Sentinel format: ``\uE000CODEGUARD:<index>\uE000``  (PUA-delimited so it can
never collide with real content and survives markdown-it parsing.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Fenced code: opening backticks/tildes (>=3), optional language, body, close.
# We do NOT use the DOTALL flag greedily across the whole doc — each fence is
# matched independently so adjacent blocks stay separate.
_FENCE_RE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})"      # opening fence at start-of-line (backticks or tildes)
    r"[ \t]*"
    r"(?P<lang>[^\n`]*)?"            # optional info string / language
    r"\n"
    r"(?P<code>.*?)"                 # body (non-greedy, DOTALL via flag)
    r"(?P=fence)"                    # matching close fence
    r"[ \t]*$",
    re.MULTILINE | re.DOTALL,
)

# Inline code spans: single or double backtick delimited. We protect these too
# so the inline pass doesn't bold/italicize/code-highlight their contents twice.
_INLINE_CODE_RE = re.compile(
    r"(?P<open>`+)"                  # one or more backticks
    r"(?!`)"                         # not followed by another backtick
    r"(?P<code>.*?)"                 # content
    r"(?<!`)"                        # close not preceded by backtick
    r"(?P=open)"                     # matching run of backticks
    r"(?!`)",
    re.DOTALL,
)

# Indented (4-space) code blocks — only treat as code when not part of a list.
# We keep this conservative: a line that starts with 4+ spaces AND is preceded
# by a blank line or another indented line counts as code. For simplicity in
# the MVP we leave indented code to markdown-it and only guard fenced + inline.

SENTINEL_PREFIX = "\uE000CODEGUARD:"
SENTINEL_SUFFIX = "\uE000"


@dataclass
class CodeSlot:
    """A protected code span extracted from the source."""

    index: int
    raw: str          # original matched text (for restoration if needed)
    code: str         # inner code (newlines preserved, rstrip trailing newline)
    lang: str | None  # info string / language (may be "")
    inline: bool      # True = inline code span, False = fenced block


def _slot_for(index: int, m: re.Match[str], inline: bool) -> CodeSlot:
    code = m.group("code")
    lang = m.groupdict().get("lang")
    if not inline:
        # Fenced block: strip exactly one trailing newline (the one before fence).
        if code.endswith("\n"):
            code = code[:-1]
        lang = lang.strip() if lang else None or None
        lang = lang or None  # "" → None
    return CodeSlot(index=index, raw=m.group(0), code=code, lang=lang, inline=inline)


def protect_code(text: str) -> tuple[str, list[CodeSlot]]:
    """Replace fenced + inline code with sentinels; return (masked_text, slots).

    Slots are ordered by extraction (fenced first, then inline). The masked
    text is safe to run through equation and markdown passes.
    """
    slots: list[CodeSlot] = []

    def _fenced_sub(m: re.Match[str]) -> str:
        idx = len(slots)
        slots.append(_slot_for(idx, m, inline=False))
        return f"{SENTINEL_PREFIX}{idx}{SENTINEL_SUFFIX}"

    masked = _FENCE_RE.sub(_fenced_sub, text)

    def _inline_sub(m: re.Match[str]) -> str:
        idx = len(slots)
        slots.append(_slot_for(idx, m, inline=True))
        return f"{SENTINEL_PREFIX}{idx}{SENTINEL_SUFFIX}"

    masked = _INLINE_CODE_RE.sub(_inline_sub, masked)
    return masked, slots


def is_sentinel(token: str) -> bool:
    """True if ``token`` looks like a code-guard sentinel."""
    return token.startswith(SENTINEL_PREFIX) and token.endswith(SENTINEL_SUFFIX)


def sentinel_index(token: str) -> int | None:
    """Extract the slot index from a sentinel token, or ``None``."""
    if not is_sentinel(token):
        return None
    core = token[len(SENTINEL_PREFIX) : -len(SENTINEL_SUFFIX)]
    try:
        return int(core)
    except ValueError:
        return None
