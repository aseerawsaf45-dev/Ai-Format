import sys
sys.path.insert(0, ".")
from app.parser.code_guard import protect_code, SENTINEL_PREFIX
from markdown_it import MarkdownIt

src = "A **bold** and *italic* and `code` line."
masked, slots = protect_code(src)

_md = MarkdownIt("commonmark", {"html": False, "linkify": False})
_md.enable("table")
_md.enable("strikethrough")

toks = _md.parse(masked, {})
for t in toks:
    if t.type == "inline":
        for c in (t.children or []):
            if c.type == "text":
                ct = c.content
                print("content repr:", repr(ct))
                print("has prefix:", SENTINEL_PREFIX in ct)
                idx = ct.find(SENTINEL_PREFIX)
                print("idx:", idx)
                if idx >= 0:
                    slice_at = ct[idx:idx+len(SENTINEL_PREFIX)]
                    print("slice repr:", repr(slice_at))
                    print("prefix repr:", repr(SENTINEL_PREFIX))
                    print("equal:", slice_at == SENTINEL_PREFIX)
                    # byte-level check
                    print("content bytes:", ct.encode("utf-8")[:30].hex())
                    print("prefix bytes:", SENTINEL_PREFIX.encode("utf-8").hex())
