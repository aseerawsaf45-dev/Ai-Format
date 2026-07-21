import docx
from app.renderer.pipeline import DiagramPipeline
from app.renderer.geometry.coord_translator import CoordTranslator
from app.renderer.ooxml.package_builder import PackageBuilder
from app.renderer.parsers.detector import detect_format

def main():
    doc = docx.Document()
    p = doc.add_paragraph()
    r = p.add_run()

    mermaid_code = '''
    graph TD
      A[Alice] --> B[Bob]
      B --> C[Charlie]
      C --> A
    '''
    
    pipeline = DiagramPipeline()
    
    # Process Diagram (Parsing -> Layout -> DrawingML)
    wpg_xml = pipeline.process(mermaid_code)
    
    # We also need to get dimensions to set wp:extent. 
    # For now, let's extract it from the pipeline model. 
    # Better architecture would be process() returning a tuple (xml, width, height) or a Result object.
    
    parser_cls = detect_format(mermaid_code)
    parser = parser_cls()
    model = parser.parse(mermaid_code)
    pipeline.text_engine.compute_node_dimensions(model)
    pipeline.layout_engine.compute_layout(model)
    
    width_emu = CoordTranslator.pt_to_emu(model.width)
    height_emu = CoordTranslator.pt_to_emu(model.height)
    
    PackageBuilder.inject_drawingml_into_run(r, wpg_xml, width_emu, height_emu)
    PackageBuilder.ensure_namespaces(doc)
    
    doc.save('test_generator_new.docx')
    print('Generated test_generator_new.docx successfully!')

if __name__ == '__main__':
    main()
