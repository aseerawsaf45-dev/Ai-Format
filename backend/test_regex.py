import sys
sys.path.insert(0, '.')
from app.parser.code_guard import protect_code
from app.parser.pipeline import parse_content

md = '''```mermaid
sequenceDiagram
User->>Server: Login
```'''

print('md:', repr(md))
masked, slots = protect_code(md)
print('masked:', repr(masked))
print('slots:', [(s.lang, s.inline) for s in slots])

doc = parse_content(md)
for b in doc.document.children:
    print(b.type, getattr(b, 'lang', None))
