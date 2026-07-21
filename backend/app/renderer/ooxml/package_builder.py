import docx
from docx.oxml import parse_xml

class PackageBuilder:
    @staticmethod
    def inject_drawingml_into_run(run, wpg_xml: str, width_emu: int, height_emu: int):
        """
        Injects the raw wpg:wgp XML into a docx Run object wrapped in a <w:drawing>.
        """
        import random
        doc_pr_id = random.randint(100000, 2000000000)
        drawing_xml = f'''
        <w:drawing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" 
                   xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" 
                   xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
                   xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" 
                   xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
            <wp:inline distT="0" distB="0" distL="0" distR="0">
                <wp:extent cx="{width_emu}" cy="{height_emu}"/>
                <wp:effectExtent l="0" t="0" r="0" b="0"/>
                <wp:docPr id="{doc_pr_id}" name="Diagram"/>
                <wp:cNvGraphicFramePr/>
                <a:graphic>
                    <a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">
                        {wpg_xml}
                    </a:graphicData>
                </a:graphic>
            </wp:inline>
        </w:drawing>
        '''
        
        run._r.append(parse_xml(drawing_xml))

    @staticmethod
    def ensure_namespaces(doc):
        """
        Ensures the document has necessary markup compatibility attributes for wpg and wps.
        """
        mc_ignorable = doc.element.get('{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable')
        if mc_ignorable is not None:
            if 'wpg' not in mc_ignorable: mc_ignorable += ' wpg'
            if 'wps' not in mc_ignorable: mc_ignorable += ' wps'
            doc.element.set('{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable', mc_ignorable)
        else:
            doc.element.set('{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable', 'wpg wps')
