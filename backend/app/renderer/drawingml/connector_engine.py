from ..models.diagram import Edge

class ConnectorEngine:
    @staticmethod
    def create_edge_xml(edge: Edge, shape_id: int, source_shape_id: int, target_shape_id: int) -> str:
        # Default connection points (e.g. idx 3=bottom, 1=top)
        # Word will auto-route it based on cxnSpPr
        
        start_idx = edge.start_anchor if edge.start_anchor is not None else 3
        end_idx = edge.end_anchor if edge.end_anchor is not None else 1
        
        cxn_xml = f'''
            <wps:cNvCnPr>
                <a:cxnSpPr>
                    <a:stCxn id="{source_shape_id}" idx="{start_idx}"/>
                    <a:endCxn id="{target_shape_id}" idx="{end_idx}"/>
                </a:cxnSpPr>
            </wps:cNvCnPr>
        '''
        
        prst_mapping = {
            "straight": "line",
            "bent": "bentConnector3",
            "curved": "curvedConnector3"
        }
        prst = prst_mapping.get(edge.connector_type, "bentConnector3")
        
        arrowhead = ""
        if edge.arrowhead_type == "normal":
            arrowhead = '<a:headEnd type="triangle"/>'
            
        return f'''
        <wps:wsp>
            <wps:cNvPr id="{shape_id}" name="Connector {shape_id}"/>
            {cxn_xml}
            <wps:spPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="100000" cy="100000"/>
                </a:xfrm>
                <a:prstGeom prst="{prst}">
                    <a:avLst/>
                </a:prstGeom>
                <a:ln w="{int((edge.style.border_width or 1.0) * 12700)}">
                    <a:solidFill>
                        <a:srgbClr val="{edge.style.border_color or '000000'}"/>
                    </a:solidFill>
                    {arrowhead}
                </a:ln>
            </wps:spPr>
            <wps:bodyPr/>
        </wps:wsp>
        '''
