import re
from typing import Union
from .base import BaseParser
from ..models.diagram import Diagram, Node, Edge

class MermaidParser(BaseParser):
    def parse(self, source: str) -> Union[Diagram, None]:
        # Basic implementation for Mermaid Flowcharts (graph TD / flowchart LR)
        diagram = Diagram()
        source = source.strip()
        
        lines = source.split('\n')
        if not lines:
            return diagram
            
        header = lines[0].strip()
        if header.startswith('graph') or header.startswith('flowchart'):
            parts = header.split()
            if len(parts) > 1:
                diagram.direction = parts[1]
                
        # Simple regex for nodes: id[label] or id(label)
        node_pattern = re.compile(r'([a-zA-Z0-9_]+)\[(.*?)\]|([a-zA-Z0-9_]+)\((.*?)\)')
        # Simple regex for edges: A --> B or A --- B
        edge_pattern = re.compile(r'([a-zA-Z0-9_]+)\s*(-+>|-+)\s*([a-zA-Z0-9_]+)')
        
        edge_counter = 0
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('%%'):
                continue
                
            # Parse edges first
            edge_match = edge_pattern.search(line)
            if edge_match:
                source_id = edge_match.group(1)
                conn = edge_match.group(2)
                target_id = edge_match.group(3)
                
                edge_id = f"e{edge_counter}"
                edge_counter += 1
                
                connector_type = "bent"
                arrowhead_type = "normal" if '>' in conn else "none"
                
                edge = Edge(id=edge_id, source_id=source_id, target_id=target_id, 
                            connector_type=connector_type, arrowhead_type=arrowhead_type)
                diagram.add_edge(edge)
                
                # Ensure nodes exist implicitly if they weren't explicitly defined
                if source_id not in diagram.nodes:
                    diagram.add_node(Node(id=source_id, label=source_id))
                if target_id not in diagram.nodes:
                    diagram.add_node(Node(id=target_id, label=target_id))
                    
            else:
                # Parse nodes
                for match in node_pattern.finditer(line):
                    if match.group(1): # id[label]
                        node_id = match.group(1)
                        label = match.group(2)
                        shape_type = "rect"
                    else: # id(label)
                        node_id = match.group(3)
                        label = match.group(4)
                        shape_type = "round_rect"
                        
                    diagram.add_node(Node(id=node_id, label=label, shape_type=shape_type))
                    
        return diagram
