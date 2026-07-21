import sys
import os

# Ensure backend module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.parser.pipeline import parse_content
from app.renderer.docx_builder import render_document

def main():
    import os
    md_path = os.path.join(os.path.dirname(__file__), 'sample_master.md')
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    response = parse_content(md_text)
    
    docx_bytes = render_document(response.document, theme_name="modern")
    
    with open('output_master.docx', 'wb') as f:
        f.write(docx_bytes)
        
    print("Document generated: output_master.docx")

if __name__ == '__main__':
    main()
