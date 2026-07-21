from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Style:
    fill_color: Optional[str] = None  # Hex color, e.g., 'FFFFFF'
    border_color: Optional[str] = None # Hex color
    border_width: Optional[float] = None
    border_style: Optional[str] = None # 'solid', 'dashed', 'dotted'
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    font_color: Optional[str] = None
    rounded_corners: bool = False
    shadow: bool = False

@dataclass
class Theme:
    default_node_style: Style = field(default_factory=Style)
    default_edge_style: Style = field(default_factory=Style)
    default_font: str = "Calibri"
