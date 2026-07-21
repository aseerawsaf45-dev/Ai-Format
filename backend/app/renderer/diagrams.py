from lxml import etree as ET
import urllib.request
import base64
import re
from io import BytesIO

EMU_PER_PIXEL = 9525

class Node:
    def __init__(self, node_id, x, y, width, height, label, shape_type, fill):
        self.id = node_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.shape_type = shape_type
        self.fill = fill

class Edge:
    def __init__(self, edge_id, source_id, target_id, path_points):
        self.id = edge_id
        self.source_id = source_id
        self.target_id = target_id
        self.path_points = path_points

class DiagramAST:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.width = 0
        self.height = 0

def fetch_svg_ast(mermaid_code: str) -> str:
    b64_code = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
    req = urllib.request.Request(
        f"https://mermaid.ink/svg/{b64_code}",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode('utf-8')

def parse_svg_to_ast(svg_xml: str) -> DiagramAST:
    # Basic SVG parser to extract nodes and edges
    ast = DiagramAST()
    
    # Remove XML namespaces to make parsing easier
    svg_xml = re.sub(r'xmlns="[^"]+"', '', svg_xml)
    root = ET.fromstring(svg_xml)
    
    # Find dimensions
    viewBox = root.get('viewBox')
    if viewBox:
        _, _, w, h = viewBox.split()
        ast.width = float(w)
        ast.height = float(h)
    
    # 1. Parse Nodes
    for g in root.findall('.//g[@class]'):
        classes = g.get('class', '')
        node_id = g.get('id', '')
        
        # Ensure it's an actual flowchart node
        if 'node' in classes and node_id.startswith('mermaid-svg-'):
            # Try to get the logical ID from mermaid (e.g. mermaid-svg-flowchart-A-0 -> A)
            logical_id = node_id.split('-')[-2] if '-' in node_id else node_id
            
            transform = g.get('transform', '')
            m = re.search(r'translate\(([^,]+),\s*([^)]+)\)', transform)
            cx, cy = 0.0, 0.0
            if m:
                cx, cy = float(m.group(1)), float(m.group(2))
            
            # Find the rect or shape inside
            rect = g.find('.//rect')
            if rect is not None:
                width = float(rect.get('width', '100'))
                height = float(rect.get('height', '50'))
                rx = cx - (width / 2)
                ry = cy - (height / 2)
                
                # Extract text
                label = ""
                foreign = g.find('.//foreignObject')
                if foreign is not None:
                    # simplistic text extraction
                    label = "".join(foreign.itertext()).strip()
                
                ast.nodes.append(Node(
                    node_id=logical_id,
                    x=rx,
                    y=ry,
                    width=width,
                    height=height,
                    label=label,
                    shape_type="rect",
                    fill="FFFFFF"
                ))
    
    # 2. Parse Edges
    for path in root.findall('.//path[@class]'):
        classes = path.get('class', '')
        parent_class = path.getparent().get('class', '') if path.getparent() is not None else ''
        if 'edgePaths' in parent_class or 'flowchart-link' in classes:
            edge_id = path.get('id', '')
            data_id = path.get('data-id', '') # e.g. L_A_B_0
            if data_id.startswith('L_'):
                parts = data_id.split('_')
                if len(parts) >= 3:
                    source_id = parts[1]
                    target_id = parts[2]
                    d = path.get('d', '')
                    ast.edges.append(Edge(edge_id, source_id, target_id, d))
                    
    return ast
