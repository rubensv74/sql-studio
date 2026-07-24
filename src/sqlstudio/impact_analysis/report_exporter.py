from pathlib import Path
from .report_generator import ImpactReportGenerator

class ImpactReportExporter:
    def export(self, result, output_file):
        html=ImpactReportGenerator().generate(result)
        output=Path(output_file)
        output.write_text(html, encoding="utf-8")
        return output
