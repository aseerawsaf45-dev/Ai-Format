from abc import ABC, abstractmethod
from typing import Union
from ..models.diagram import Diagram
from ..models.chart import Chart

class BaseParser(ABC):
    """
    Abstract base class for all diagram parsers.
    """
    @abstractmethod
    def parse(self, source: str) -> Union[Diagram, Chart]:
        """
        Parses the source code string into a Semantic Model (Diagram or Chart).
        """
        pass
