import random
from typing import List
from lxml import etree as ET

class DrawingMLGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.emu_per_pixel = 9525
        self.shape_id_counter = random.randint(100000, 2000000000)

    def get_next_id(self):
        self.shape_id_counter += 1
        return self.shape_id_counter

    def escape(self, text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def build_xml(self) -> str:
        # Find max bounds
        max_w = max([n.x + n.width for n in self.ast.nodes] + [0])
        max_h = max([n.y + n.height for n in self.ast.nodes] + [0])
        
        # Adding margins
        total_cx = int(max_w * self.emu_per_pixel) + 100000
        total_cy = int(max_h * self.emu_per_pixel) + 100000

        # We will use wpg:wgp to group everything
        xml = f'''
        <wpg:wgp xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
                 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">
            <wpg:cNvPr id="{self.get_next_id()}" name="DiagramGroup"/>
            <wpg:cNvGrpSpPr/>
            <wpg:grpSpPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="{total_cx}" cy="{total_cy}"/>
                    <a:chOff x="0" y="0"/>
                    <a:chExt cx="{total_cx}" cy="{total_cy}"/>
                </a:xfrm>
            </wpg:grpSpPr>
        '''
        
        # 1. Map Logical IDs to numeric Shape IDs
        node_id_map = {}
        for node in self.ast.nodes:
            sid = self.get_next_id()
            node_id_map[node.id] = sid
            xml += self.build_node(node, sid)
            
        # 2. Build Edges
        for edge in self.ast.edges:
            if edge.source_id in node_id_map and edge.target_id in node_id_map:
                xml += self.build_edge(edge, node_id_map[edge.source_id], node_id_map[edge.target_id])
                
        xml += '''
        </wpg:wgp>
        '''
        return xml

    def build_node(self, node, shape_id) -> str:
        x_emu = int(node.x * self.emu_per_pixel)
        y_emu = int(node.y * self.emu_per_pixel)
        cx_emu = int(node.width * self.emu_per_pixel)
        cy_emu = int(node.height * self.emu_per_pixel)
        
        label = self.escape(node.label)
        
        # Map shape
        prst = "rect"
        
        return f'''
        <wps:wsp>
            <wps:cNvPr id="{shape_id}" name="Node {shape_id}"/>
            <wps:cNvSpPr/>
            <wps:spPr>
                <a:xfrm>
                    <a:off x="{x_emu}" y="{y_emu}"/>
                    <a:ext cx="{cx_emu}" cy="{cy_emu}"/>
                </a:xfrm>
                <a:prstGeom prst="{prst}">
                    <a:avLst/>
                </a:prstGeom>
                <a:solidFill>
                    <a:srgbClr val="FFFFFF"/>
                </a:solidFill>
                <a:ln w="12700">
                    <a:solidFill>
                        <a:srgbClr val="000000"/>
                    </a:solidFill>
                </a:ln>
            </wps:spPr>
            <wps:txbx>
                <w:txbxContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                    <w:p>
                        <w:pPr>
                            <w:jc w:val="center"/>
                            <w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>
                        </w:pPr>
                        <w:r>
                            <w:t>{label}</w:t>
                        </w:r>
                    </w:p>
                </w:txbxContent>
            </wps:txbx>
            <wps:bodyPr rtlCol="0" anchor="ctr"/>
        </wps:wsp>
        '''

    def build_edge(self, edge, source_shape_id, target_shape_id) -> str:
        # Default connection points (e.g. idx 3=bottom, 1=top)
        # We need a robust mapping depending on direction, but for now we link them loosely
        # and let Word compute the line. 
        # Actually Word will snap it to the edge if we provide stCxn.
        
        # WordprocessingGroup does not fully support routed connectors. 
        # Using wps:cNvCnPr inside wpg:wgp causes Word to report unreadable content.
        # We must use standard wps:cNvSpPr for the line.
        cxn_xml = f'''
            <wps:cNvSpPr/>
        '''
        
        # A bent connector
        prst = "bentConnector3"
        
        # Generate the geometry of the line (just a bounding box encompassing start/end)
        # Word will auto-route it based on cxnSpPr when opened!
        # But we should give it a nominal bounds so it's valid XML
        
        return f'''
        <wps:wsp>
            <wps:cNvPr id="{self.get_next_id()}" name="Connector {self.get_next_id()}"/>
            {cxn_xml}
            <wps:spPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="100000" cy="100000"/>
                </a:xfrm>
                <a:prstGeom prst="{prst}">
                    <a:avLst/>
                </a:prstGeom>
                <a:ln w="12700">
                    <a:solidFill>
                        <a:srgbClr val="000000"/>
                    </a:solidFill>
                </a:ln>
            </wps:spPr>
            <wps:bodyPr/>
        </wps:wsp>
        '''
