from __future__ import annotations

from pathlib import Path

from .models import ImpactResult
from .report_generator import ImpactReportGenerator


class ImpactReportExporter:
    """Persist an impact report as a self-contained HTML file."""

    def export(self, result: ImpactResult, output_file: str | Path) -> Path:
        output = Path(output_file)
        output.parent.mkdir(parents=True, exist_ok=True)
        html = ImpactReportGenerator().generate(result)
        output.write_text(html, encoding="utf-8")
        return output
