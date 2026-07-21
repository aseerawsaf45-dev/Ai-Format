"""Document theme presets.

A :class:`Theme` carries the typographic + color choices the renderer applies
to the python-docx document. Each named preset is a tuned combination; users
pick one before export (the frontend exposes them via the ThemePicker).

All hex colors are 6-digit, no leading ``#`` — that's what OOXML expects.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Theme:
    """Visual settings for a rendered document."""

    name: str
    label: str
    # Body / heading typography.
    body_font: str = "Calibri"
    body_size_pt: float = 11.0
    heading_font: str = "Calibri"
    base_heading_size_pt: float = 16.0  # h1; others scale down from this.
    # Colors (hex, no '#').
    body_color: str = "1F1F1F"
    heading_color: str = "1F3864"
    accent: str = "2E74B5"
    link_color: str = "0563C1"
    # Block elements.
    code_bg: str = "transparent"
    code_fg: str = "333333"
    code_lang_color: str = "006699"
    quote_bg: str = "F4F4F4"
    quote_border: str = "A6A6A6"
    table_header_bg: str = "2E74B5"
    table_header_fg: str = "FFFFFF"
    table_band_bg: str = "F2F2F2"
    table_border: str = "BFBFBF"
    # Page.
    margin_inches: float = 1.0

    def heading_size(self, level: int) -> float:
        """Heading font size for a given level (1-6)."""
        # h1 = base, each step down shrinks ~12%.
        scale = {1: 1.0, 2: 0.87, 3: 0.75, 4: 0.65, 5: 0.58, 6: 0.52}
        return round(self.base_heading_size_pt * scale.get(level, 0.52), 1)


THEMES: dict[str, Theme] = {
    "modern": Theme(
        name="modern",
        label="Modern",
        body_font="Calibri",
        heading_font="Calibri",
        heading_color="1F3864",
        accent="2E74B5",
    ),
    "academic": Theme(
        name="academic",
        label="Academic",
        body_font="Cambria",
        heading_font="Cambria",
        body_size_pt=12.0,
        base_heading_size_pt=15.0,
        body_color="000000",
        heading_color="000000",
        accent="000000",
        table_header_bg="404040",
        margin_inches=1.0,
    ),
    "corporate": Theme(
        name="corporate",
        label="Corporate",
        body_font="Calibri",
        heading_font="Calibri",
        heading_color="1A1A1A",
        accent="0F6CBD",
        table_header_bg="0F6CBD",
    ),
    "minimal": Theme(
        name="minimal",
        label="Minimal",
        body_font="Calibri",
        heading_font="Calibri",
        body_color="333333",
        heading_color="111111",
        accent="666666",
        table_header_bg="EFEFEF",
        table_header_fg="111111",
        table_band_bg="FAFAFA",
    ),
}


def get_theme(name: str) -> Theme:
    """Resolve a theme by name, falling back to ``modern``."""
    return THEMES.get(name, THEMES["modern"])
