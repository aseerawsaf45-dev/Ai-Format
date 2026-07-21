import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from ..models.diagram import Node
from ..geometry.coord_translator import CoordTranslator

class ShapeFactory:
    @staticmethod
    def _map_shape_type(shape_type: str) -> str:
        mapping = {
            "rect": "rect",
            "round_rect": "roundRect",
            "circle": "ellipse",
            "diamond": "diamond",
            "cylinder": "cylinder",
            "parallelogram": "parallelogram",
            "trapezoid": "trapezoid",
            "document": "document",
            "subprocess": "proc",
        }
        return mapping.get(shape_type, "rect")

    @staticmethod
    def create_node_xml(node: Node, shape_id: int) -> str:
        x_emu = CoordTranslator.pt_to_emu(node.x)
        y_emu = CoordTranslator.pt_to_emu(node.y)
        cx_emu = CoordTranslator.pt_to_emu(node.width)
        cy_emu = CoordTranslator.pt_to_emu(node.height)
        
        prst = ShapeFactory._map_shape_type(node.shape_type)
        label = escape(node.label or "")
        
        # Word DrawingML snippet for a node with text
        xml = f'''
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
                    <a:srgbClr val="{node.style.fill_color or 'FFFFFF'}"/>
                </a:solidFill>
                <a:ln w="{int((node.style.border_width or 1.0) * 12700)}">
                    <a:solidFill>
                        <a:srgbClr val="{node.style.border_color or '000000'}"/>
                    </a:solidFill>
                </a:ln>
            </wps:spPr>
            <wps:txbx>
                <w:txbxContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                    <w:p>
                        <w:pPr>
                            <w:jc w:val="center"/>
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
        return xml
