import sys; sys.path.insert(0, '.')
from app.parser.pipeline import parse_content
from app.renderer.docx_builder import render_document

md = "Matrix example:\n\n$$\\begin{bmatrix} 1 & 2 \\\\ 3 & 4 \\end{bmatrix}$$\n\nQuadratic formula:\n\n$$\\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$\n\nInline: the formula $E = mc^2$ is famous.\n"

result = parse_content(md)
print("Parse result children:")
for b in result.document.children:
    t = b.type
    print(f"  {t}", end='')
    if t == 'block_equation':
        print(f"  omml={'OK' if b.omml else 'NONE'}", end='')
        if b.omml:
            print(f"  omml_start: {b.omml[:50]}", end='')
    print()

print("\nRendering to DOCX...")
try:
    docx_bytes = render_document(result.document, 'modern')
    with open('_test_matrix.docx', 'wb') as f:
        f.write(docx_bytes)
    print(f"SUCCESS — wrote _test_matrix.docx ({len(docx_bytes)} bytes)")
except Exception as e:
    import traceback
    print("FAILED:")
    traceback.print_exc()
