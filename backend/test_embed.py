import docx
from docx.opc.part import Part
from docx.opc.packuri import PackURI

doc = docx.Document()
svg_data = b'<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg>'

partname = PackURI('/word/media/image1.svg')
svg_part = Part(partname, 'image/svg+xml', svg_data, doc.part.package)

rel = doc.part.relate_to(svg_part, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image')
print('Rel ID:', rel)
doc.save('test_svg_embed.docx')
