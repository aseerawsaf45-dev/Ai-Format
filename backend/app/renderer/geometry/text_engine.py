from ..models.diagram import Diagram

class TextEngine:
    def __init__(self, default_font="Calibri", default_size=11):
        self.default_font = default_font
        self.default_size = default_size
        
        # A simple heuristic for text width in points.
        # Calibri 11pt is roughly 6-7 pixels per character on average.
        self.char_width_pts = 7.0
        self.line_height_pts = 15.0

    def compute_node_dimensions(self, diagram: Diagram):
        """
        Computes the width and height of each node based on its label.
        """
        padding_x = 20.0
        padding_y = 15.0
        min_width = 80.0
        min_height = 40.0
        
        for node in diagram.nodes.values():
            label = node.label or ""
            lines = label.split('\n')
            
            max_line_len = max([len(line) for line in lines] + [0])
            
            calc_w = (max_line_len * self.char_width_pts) + (padding_x * 2)
            calc_h = (len(lines) * self.line_height_pts) + (padding_y * 2)
            
            node.width = max(min_width, calc_w)
            node.height = max(min_height, calc_h)
