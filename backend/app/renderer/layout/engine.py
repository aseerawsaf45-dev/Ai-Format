from abc import ABC, abstractmethod
from ..models.diagram import Diagram

class LayoutEngine(ABC):
    @abstractmethod
    def compute_layout(self, diagram: Diagram):
        """
        Computes the X, Y, Width, and Height for all nodes in the diagram.
        Modifies the diagram object in-place.
        """
        pass

class DummyLayoutEngine(LayoutEngine):
    """
    A temporary layout engine that just places nodes in a grid.
    In a real implementation, this would use a graph layout algorithm like Dagre.
    """
    def compute_layout(self, diagram: Diagram):
        x, y = 50.0, 50.0
        max_w = 0.0
        max_h = 0.0
        
        spacing_x = 150.0
        spacing_y = 100.0
        
        items_per_row = 3
        count = 0
        
        for node in diagram.nodes.values():
            node.x = x
            node.y = y
            # Width and height should be pre-computed by the TextEngine
            
            x += spacing_x
            max_w = max(max_w, node.x + node.width)
            max_h = max(max_h, node.y + node.height)
            
            count += 1
            if count >= items_per_row:
                x = 50.0
                y += spacing_y
                count = 0
                
        diagram.width = max_w + 50.0
        diagram.height = max_h + 50.0
