import base64
import urllib.request

def fetch_svg(code):
    b64 = base64.urlsafe_b64encode(code.encode('utf-8')).decode('utf-8')
    req = urllib.request.Request(
        f"https://mermaid.ink/svg/{b64}",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode('utf-8')

code = """
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process]
    B -->|No| D[End]
"""
svg = fetch_svg(code)
with open("test.svg", "w") as f:
    f.write(svg)
print(svg[:500])
