from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DataPoint:
    label: str
    value: float

@dataclass
class Series:
    name: str
    points: List[DataPoint] = field(default_factory=list)

@dataclass
class Chart:
    chart_type: str = "bar" # bar, column, line, pie, etc.
    title: Optional[str] = None
    series: List[Series] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    width: float = 500.0
    height: float = 300.0
