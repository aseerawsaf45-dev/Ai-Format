from .parsers.detector import detect_format
from .geometry.text_engine import TextEngine
from .layout.engine import DummyLayoutEngine
from .drawingml.generator import DrawingMLGenerator
from .models.diagram import Diagram

class DiagramPipeline:
    def __init__(self):
        self.text_engine = TextEngine()
        self.layout_engine = DummyLayoutEngine() # Replace with actual dagre/elk layout later
        self.drawingml_gen = DrawingMLGenerator()

    def process(self, source: str) -> str:
        """
        Takes raw DSL source code and returns the complete DrawingML <wpg:wgp> XML string.
        """
        parser_cls = detect_format(source)
        if not parser_cls:
            raise ValueError("Unsupported diagram format.")
            
        parser = parser_cls()
        model = parser.parse(source)
        
        if isinstance(model, Diagram):
            # 1. Measure text & set initial dimensions
            self.text_engine.compute_node_dimensions(model)
            
            # 2. Compute Layout (positioning)
            self.layout_engine.compute_layout(model)
            
            # 3. Generate XML
            xml_str = self.drawingml_gen.generate(model)
            
            return xml_str
        else:
            raise NotImplementedError("Charts processing pipeline not yet connected.")
