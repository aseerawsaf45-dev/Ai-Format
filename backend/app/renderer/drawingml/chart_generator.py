from ..models.chart import Chart

class ChartGenerator:
    @staticmethod
    def generate(chart: Chart) -> str:
        """
        Stub for generating OOXML charts.
        Returns a minimal c:chartSpace XML string.
        """
        # In a full implementation, this will construct the entire chart1.xml 
        return "<c:chartSpace xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\"></c:chartSpace>"
