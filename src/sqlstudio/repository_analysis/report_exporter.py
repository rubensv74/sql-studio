from __future__ import annotations

from pathlib import Path

from .models import RepositoryAnalysisResult
from .report_generator import RepositoryAnalysisReportGenerator


class RepositoryAnalysisReportExporter:
    """Persist a self-contained repository-analysis HTML report."""

    def export(
        self,
        result: RepositoryAnalysisResult,
        output_file: str | Path,
    ) -> Path:
        output = Path(output_file)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            RepositoryAnalysisReportGenerator().generate(result),
            encoding="utf-8",
        )
        return output
