from ..models.diagram import Diagram
from ..geometry.coord_translator import CoordTranslator
from .shape_factory import ShapeFactory
from .connector_engine import ConnectorEngine

class DrawingMLGenerator:
    def __init__(self):
        self.shape_id_counter = 1000

    def _get_next_id(self):
        self.shape_id_counter += 1
        return self.shape_id_counter

    def generate(self, diagram: Diagram) -> str:
        total_cx = CoordTranslator.pt_to_emu(diagram.width)
        total_cy = CoordTranslator.pt_to_emu(diagram.height)

        xml = f'''
        <wpg:wgp xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
                 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">
            <wpg:cNvPr id="{self._get_next_id()}" name="DiagramGroup"/>
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
        
        # Keep track of mapping logical ID to DrawingML numeric Shape ID
        node_id_map = {}
        for node_id, node in diagram.nodes.items():
            sid = self._get_next_id()
            node_id_map[node_id] = sid
            xml += ShapeFactory.create_node_xml(node, sid)
            
        for edge in diagram.edges:
            if edge.source_id in node_id_map and edge.target_id in node_id_map:
                sid = self._get_next_id()
                xml += ConnectorEngine.create_edge_xml(
                    edge, sid, 
                    node_id_map[edge.source_id], 
                    node_id_map[edge.target_id]
                )
                
        xml += '''
        </wpg:wgp>
        '''
        return xml
