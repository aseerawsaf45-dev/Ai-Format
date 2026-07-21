import re
from typing import Optional, Type
from .base import BaseParser
from .mermaid import MermaidParser

def detect_format(source: str) -> Optional[Type[BaseParser]]:
    """
    Detects the format of the diagram source and returns the appropriate parser class.
    """
    source_trimmed = source.strip()
    
    # Simple heuristic for Mermaid
    if re.search(r'^\s*(graph|flowchart|sequenceDiagram|gantt|classDiagram|stateDiagram|pie|journey|mindmap|erDiagram)', source_trimmed, re.IGNORECASE | re.MULTILINE):
        return MermaidParser
    
    # Stub for plantUML
    if source_trimmed.startswith('@startuml'):
        pass # return PlantUMLParser
        
    return None
