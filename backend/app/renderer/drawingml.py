import re
import xml.etree.ElementTree as ET
from docx.oxml import parse_xml

EMU_PER_PIXEL = 9525  # standard 96 DPI conversion

def _create_shape(shape_id, x, y, w, h, text, shape_type="rect", fill="F4F4F4"):
    """Generate a single wps:wsp WordprocessingShape."""
    # Convert pixels to EMU
    x_emu = int(x * EMU_PER_PIXEL)
    y_emu = int(y * EMU_PER_PIXEL)
    w_emu = int(w * EMU_PER_PIXEL)
    h_emu = int(h * EMU_PER_PIXEL)
    
    xml = f'''
    <wps:wsp xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
             xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <wps:cNvPr id="{shape_id}" name="Shape {shape_id}"/>
        <wps:cNvSpPr/>
        <wps:spPr>
            <a:xfrm>
                <a:off x="{x_emu}" y="{y_emu}"/>
                <a:ext cx="{w_emu}" cy="{h_emu}"/>
            </a:xfrm>
            <a:prstGeom prst="{shape_type}">
                <a:avLst/>
            </a:prstGeom>
            <a:solidFill>
                <a:srgbClr val="{fill}"/>
            </a:solidFill>
            <a:ln w="12700">
                <a:solidFill>
                    <a:srgbClr val="000000"/>
                </a:solidFill>
            </a:ln>
        </wps:spPr>
        <wps:txbx>
            <w:txbxContent>
                <w:p>
                    <w:pPr>
                        <w:jc w:val="center"/>
                    </w:pPr>
                    <w:r>
                        <w:rPr>
                            <w:sz w:val="20"/>
                            <w:color w:val="000000"/>
                        </w:rPr>
                        <w:t>{text}</w:t>
                    </w:r>
                </w:p>
            </w:txbxContent>
        </wps:txbx>
    </wps:wsp>
    '''
    return xml

def _create_connector(cxn_id, d_path):
    """Generate a wps:wsp connector from an SVG path d attribute."""
    # A simple straight connector based on first and last point of the path
    # d="M 35,40 L 35,70" or "M10,20C10,30..."
    nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", d_path)]
    if len(nums) < 4:
        return ""
    start_x, start_y = nums[0], nums[1]
    end_x, end_y = nums[-2], nums[-1]
    
    x = min(start_x, end_x)
    y = min(start_y, end_y)
    w = max(abs(start_x - end_x), 1)  # avoid 0 width
    h = max(abs(start_y - end_y), 1)  # avoid 0 height
    
    x_emu = int(x * EMU_PER_PIXEL)
    y_emu = int(y * EMU_PER_PIXEL)
    w_emu = int(w * EMU_PER_PIXEL)
    h_emu = int(h * EMU_PER_PIXEL)
    
    xml = f'''
    <wps:wsp xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
        <wps:cNvPr id="{cxn_id}" name="Connector {cxn_id}"/>
        <wps:cNvSpPr/>
        <wps:spPr>
            <a:xfrm>
                <a:off x="{x_emu}" y="{y_emu}"/>
                <a:ext cx="{w_emu}" cy="{h_emu}"/>
            </a:xfrm>
            <a:prstGeom prst="line">
                <a:avLst/>
            </a:prstGeom>
            <a:ln w="12700">
                <a:solidFill>
                    <a:srgbClr val="000000"/>
                </a:solidFill>
                <a:headEnd type="none"/>
                <a:tailEnd type="triangle"/>
            </a:ln>
        </wps:spPr>
    </wps:wsp>
    '''
    return xml

def _parse_color(style_str, default="F4F4F4"):
    m = re.search(r"fill:\s*#([0-9a-fA-F]{6})", style_str)
    if m:
        return m.group(1).upper()
    return default

def _create_text_box(shape_id, x, y, text, font_size=12, align="center"):
    # Create a transparent shape with just text
    x_emu = int(x * EMU_PER_PIXEL)
    y_emu = int(y * EMU_PER_PIXEL)
    # Estimate width/height
    w_emu = int(len(text) * font_size * 0.6 * EMU_PER_PIXEL)
    h_emu = int(font_size * 1.5 * EMU_PER_PIXEL)
    
    xml = f'''
    <wps:wsp xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
             xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <wps:cNvPr id="{shape_id}" name="Text {shape_id}"/>
        <wps:cNvSpPr txBox="1"/>
        <wps:spPr>
            <a:xfrm>
                <a:off x="{x_emu}" y="{y_emu}"/>
                <a:ext cx="{w_emu}" cy="{h_emu}"/>
            </a:xfrm>
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
            <a:noFill/>
            <a:ln><a:noFill/></a:ln>
        </wps:spPr>
        <wps:txbx>
            <w:txbxContent>
                <w:p>
                    <w:pPr><w:jc w:val="{align}"/></w:pPr>
                    <w:r><w:t>{text}</w:t></w:r>
                </w:p>
            </w:txbxContent>
        </wps:txbx>
    </wps:wsp>
    '''
    return xml

def _create_line(shape_id, x1, y1, x2, y2, dashed=False):
    x = min(x1, x2)
    y = min(y1, y2)
    w = max(abs(x1 - x2), 1)
    h = max(abs(y1 - y2), 1)
    
    x_emu = int(x * EMU_PER_PIXEL)
    y_emu = int(y * EMU_PER_PIXEL)
    w_emu = int(w * EMU_PER_PIXEL)
    h_emu = int(h * EMU_PER_PIXEL)
    
    dash_xml = '<a:prstDash val="dash"/>' if dashed else ''
    
    xml = f'''
    <wps:wsp xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
        <wps:cNvPr id="{shape_id}" name="Line {shape_id}"/>
        <wps:cNvSpPr/>
        <wps:spPr>
            <a:xfrm>
                <a:off x="{x_emu}" y="{y_emu}"/>
                <a:ext cx="{w_emu}" cy="{h_emu}"/>
            </a:xfrm>
            <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
            <a:ln w="12700">
                <a:solidFill><a:srgbClr val="000000"/></a:solidFill>
                {dash_xml}
                <a:headEnd type="none"/>
                <a:tailEnd type="triangle"/>
            </a:ln>
        </wps:spPr>
    </wps:wsp>
    '''
    return xml

def svg_to_drawingml(svg_string: str):
    svg_string = re.sub(r'\sxmlns="[^"]+"', '', svg_string, count=1)
    try:
        root = ET.fromstring(svg_string)
    except Exception as e:
        print("Failed to parse SVG:", e)
        return None
        
    viewbox = root.attrib.get('viewBox')
    if viewbox:
        _, _, w_str, h_str = viewbox.split()
        total_w, total_h = float(w_str), float(h_str)
    else:
        total_w, total_h = 800, 600
        
    grp_w_emu = int(total_w * EMU_PER_PIXEL)
    grp_h_emu = int(total_h * EMU_PER_PIXEL)
    
    shapes_xml = []
    shape_id = 100
    
    # Generic SVG parsing
    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        style = elem.attrib.get('style', '')
        cls = elem.attrib.get('class', '')
        
        # Determine global translation if inside a <g>
        tx, ty = 0, 0
        parent = elem # rough approximation, actual SVG requires walking up tree
        # For simplicity in Mermaid, translation is usually on the immediate <g> parent
        
        if tag == 'rect':
            x = float(elem.attrib.get('x', 0))
            y = float(elem.attrib.get('y', 0))
            w = float(elem.attrib.get('width', 50))
            h = float(elem.attrib.get('height', 30))
            fill = _parse_color(style, "FFFFFF" if "actor" in cls else "F4F4F4")
            shapes_xml.append(_create_shape(shape_id, x, y, w, h, "", "rect", fill))
            shape_id += 1
            
        elif tag == 'circle':
            cx = float(elem.attrib.get('cx', 0))
            cy = float(elem.attrib.get('cy', 0))
            r = float(elem.attrib.get('r', 20))
            fill = _parse_color(style)
            shapes_xml.append(_create_shape(shape_id, cx-r, cy-r, r*2, r*2, "", "ellipse", fill))
            shape_id += 1
            
        elif tag == 'polygon':
            points = elem.attrib.get('points', '')
            nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", points)]
            if nums:
                xs = nums[0::2]
                ys = nums[1::2]
                x, y = min(xs), min(ys)
                w, h = max(xs)-x, max(ys)-y
                fill = _parse_color(style)
                shapes_xml.append(_create_shape(shape_id, x, y, w, h, "", "diamond", fill))
                shape_id += 1
                
        elif tag == 'line':
            x1 = float(elem.attrib.get('x1', 0))
            y1 = float(elem.attrib.get('y1', 0))
            x2 = float(elem.attrib.get('x2', 0))
            y2 = float(elem.attrib.get('y2', 0))
            dashed = "dash" in style or "dash" in elem.attrib.get('stroke-dasharray', '')
            shapes_xml.append(_create_line(shape_id, x1, y1, x2, y2, dashed))
            shape_id += 1
            
        elif tag == 'text':
            x = float(elem.attrib.get('x', 0))
            y = float(elem.attrib.get('y', 0)) - 12 # Adjust baseline
            text = elem.text or ""
            if text:
                shapes_xml.append(_create_text_box(shape_id, x - 20, y, text))
                shape_id += 1
                
        elif tag == 'path':
            # Only process if it looks like an edge
            if 'edge' in cls or 'messageLine' in cls:
                d = elem.attrib.get('d', '')
                dashed = "dash" in style
                shapes_xml.append(_create_connector(shape_id, d))
                shape_id += 1
                
    # Also parse flowcharts which nest <text> inside <g class="node">
    for g in root.findall(".//g"):
        if 'node' in g.attrib.get('class', ''):
            transform = g.attrib.get('transform', '')
            m = re.search(r"translate\(([\d\.]+),\s*([\d\.]+)\)", transform)
            if m:
                tx, ty = float(m.group(1)), float(m.group(2))
                text_elems = g.findall(".//tspan")
                text = " ".join([t.text for t in text_elems if getattr(t, 'text', None)])
                if not text:
                    text_node = g.find(".//text")
                    text = text_node.text if getattr(text_node, 'text', None) else ""
                if text:
                    shapes_xml.append(_create_text_box(shape_id, tx-20, ty-10, text))
                    shape_id += 1
                    
    shapes_joined = "".join(shapes_xml)
    
    xml = f'''
    <w:drawing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
               xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
               xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
      <wp:inline distT="0" distB="0" distL="0" distR="0">
        <wp:extent cx="{grp_w_emu}" cy="{grp_h_emu}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:docPr id="1" name="Mermaid Diagram"/>
        <wp:cNvGraphicFramePr/>
        <a:graphic>
          <a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">
            <wpg:wgp>
              <wpg:cNvGrpSpPr/>
              <wpg:grpSpPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="{grp_w_emu}" cy="{grp_h_emu}"/>
                  <a:chOff x="0" y="0"/>
                  <a:chExt cx="{grp_w_emu}" cy="{grp_h_emu}"/>
                </a:xfrm>
              </wpg:grpSpPr>
              {shapes_joined}
            </wpg:wgp>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
    '''
    return parse_xml(xml)
