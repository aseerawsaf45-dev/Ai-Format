from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .style import Style

@dataclass
class Node:
    id: str
    label: str
    shape_type: str = "rect" # rect, circle, diamond, cylinder, etc.
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 50.0
    parent_id: Optional[str] = None
    style: Style = field(default_factory=Style)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Edge:
    id: str
    source_id: str
    target_id: str
    label: Optional[str] = None
    connector_type: str = "bent" # straight, bent, curved
    arrowhead_type: str = "normal" # normal, none, dot, etc.
    path_points: List[tuple] = field(default_factory=list) # Custom routed points if any
    style: Style = field(default_factory=Style)
    start_anchor: Optional[int] = None
    end_anchor: Optional[int] = None

@dataclass
class Group(Node):
    children: List[str] = field(default_factory=list)
    # A group is a special node that acts as a container for other nodes.

@dataclass
class Diagram:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    groups: Dict[str, Group] = field(default_factory=dict)
    width: float = 0.0
    height: float = 0.0
    direction: str = "TB" # TB, LR, RL, BT
    theme: Optional[str] = None

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

    def add_group(self, group: Group):
        self.groups[group.id] = group
