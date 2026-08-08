from __future__ import annotations

from html import escape

from .models import RepositoryAnalysisResult


class RepositoryAnalysisReportGenerator:
    """Generate a self-contained human-readable repository analysis report."""

    def generate(self, result: RepositoryAnalysisResult) -> str:
        summary = self._summary_cards(result)
        sources = self._source_table(result)
        dependency_overview = self._dependency_table(result)
        key_objects = self._key_objects_table(result)
        cycles = self._cycles_panel(result)
        dead_objects = self._dead_objects_panel(result)
        findings = self._findings_table(result)
        uncertainty = self._uncertainty_panel(result)
        objects = self._object_explorer(result)
        traceability = self._traceability_table(result)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SQL Studio · Repository Analysis</title>
<style>
:root {{
  color-scheme: light;
  --bg: #f5f7fa;
  --surface: #ffffff;
  --border: #e2e8f0;
  --text: #0f172a;
  --muted: #64748b;
  --primary: #2563eb;
  --primary-soft: #eff6ff;
  --error: #b91c1c;
  --error-soft: #fef2f2;
  --warning: #a16207;
  --warning-soft: #fefce8;
  --info: #0369a1;
  --info-soft: #f0f9ff;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--text); font-family: Inter, "Segoe UI", Arial, sans-serif; }}
main {{ max-width: 1480px; margin: 0 auto; padding: 36px 24px 64px; }}
header {{ margin-bottom: 24px; }}
h1 {{ margin: 0 0 8px; font-size: 30px; }}
h2 {{ margin: 0 0 16px; font-size: 19px; }}
p {{ line-height: 1.55; }}
.subtitle, .muted {{ color: var(--muted); }}
.metrics {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin-bottom: 24px; }}
.metric, .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; }}
.metric {{ padding: 16px; }}
.metric .label {{ display: block; color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }}
.metric strong {{ display: block; margin-top: 7px; font-size: 26px; }}
.panel {{ padding: 20px; margin-bottom: 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }}
.table-wrap {{ overflow: auto; max-height: 560px; border: 1px solid var(--border); border-radius: 10px; }}
table {{ width: 100%; border-collapse: collapse; min-width: 760px; background: var(--surface); }}
th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
th {{ position: sticky; top: 0; background: #f8fafc; color: var(--muted); font-size: 12px; text-transform: uppercase; z-index: 1; }}
td.code, code {{ font-family: Consolas, "SFMono-Regular", monospace; font-size: 13px; }}
.badge {{ display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }}
.badge.error {{ background: var(--error-soft); color: var(--error); }}
.badge.warning {{ background: var(--warning-soft); color: var(--warning); }}
.badge.info {{ background: var(--info-soft); color: var(--info); }}
.badge.neutral {{ background: #f1f5f9; color: #475569; }}
.warning-box {{ padding: 14px 16px; border-left: 4px solid var(--warning); background: var(--warning-soft); border-radius: 8px; margin-bottom: 14px; }}
.error-box {{ padding: 14px 16px; border-left: 4px solid var(--error); background: var(--error-soft); border-radius: 8px; margin-bottom: 14px; }}
.empty {{ margin: 0; color: var(--muted); }}
ul.clean {{ margin: 0; padding-left: 20px; }}
input[type="search"] {{ width: min(520px, 100%); padding: 10px 12px; margin-bottom: 12px; border: 1px solid var(--border); border-radius: 9px; font: inherit; background: #fff; }}
.small {{ font-size: 12px; }}
@media (max-width: 1100px) {{ .metrics {{ grid-template-columns: repeat(3, 1fr); }} }}
@media (max-width: 760px) {{ main {{ padding: 24px 14px 40px; }} .metrics, .grid {{ grid-template-columns: 1fr; }} table {{ min-width: 680px; }} }}
</style>
</head>
<body>
<main>
<header>
  <h1>SQL Studio · Análisis del repositorio</h1>
  <p class="subtitle">Vista unificada del inventario, dependencias, riesgos estáticos y trazabilidad de fuentes.</p>
</header>
<section aria-label="Resumen ejecutivo">{summary}</section>
<section class="panel" id="inventory"><h2>1. Inventario del repositorio</h2>{sources}</section>
<section class="panel" id="dependencies"><h2>2. Mapa de dependencias</h2><p class="muted small">Dirección canónica: <code>source -&gt; target</code>; el origen depende del destino.</p>{dependency_overview}</section>
<section class="panel" id="key-objects"><h2>3. Objetos clave</h2><p class="muted small">Ordenados por número de dependientes directos. Es una señal de centralidad, no una severidad.</p>{key_objects}</section>
<section class="grid">
  <section class="panel" id="cycles"><h2>4. Dependencias circulares</h2>{cycles}</section>
  <section class="panel" id="dead"><h2>5. Candidatos a objetos no utilizados</h2>{dead_objects}</section>
</section>
<section class="panel" id="findings"><h2>6. Hallazgos por severidad</h2>{findings}</section>
<section class="panel" id="uncertainty"><h2>7. SQL dinámico e incertidumbre</h2>{uncertainty}</section>
<section class="panel" id="objects"><h2>8. Explorador de objetos</h2>{objects}</section>
<section class="panel" id="traceability"><h2>9. Trazabilidad de fuentes</h2>{traceability}</section>
</main>
<script>
function filterObjects() {{
  const input = document.getElementById('object-search');
  const needle = (input.value || '').toLowerCase();
  document.querySelectorAll('#object-table tbody tr').forEach(function(row) {{
    row.hidden = !row.textContent.toLowerCase().includes(needle);
  }});
}}
</script>
</body>
</html>"""

    def _summary_cards(self, result: RepositoryAnalysisResult) -> str:
        values = (
            ("Fuentes SQL", result.source_count),
            ("Objetos", result.parsed_object_count),
            ("Dependencias", len(result.graph.edges)),
            ("Ciclos", len(result.cycles)),
            ("Candidatos", len(result.dead_objects.findings)),
            ("Hallazgos", len(result.static_analysis.findings)),
            ("Errores", result.static_analysis.count("error")),
            ("Avisos", result.static_analysis.count("warning")),
            ("Info", result.static_analysis.count("info")),
            ("SQL dinámico", len(result.dynamic_sql_objects)),
            ("Nodos del grafo", len(result.graph.nodes)),
            ("Objetos durables", result.durable_object_count),
        )
        return '<div class="metrics">' + "".join(self._metric(label, value) for label, value in values) + "</div>"

    @staticmethod
    def _metric(label: str, value: int) -> str:
        return f'<article class="metric"><span class="label">{escape(label)}</span><strong>{value}</strong></article>'

    def _source_table(self, result: RepositoryAnalysisResult) -> str:
        rows = "".join(
            "<tr>"
            f'<td class="code">{escape(source.source_id)}</td>'
            f'<td class="code">{escape(source.path or "—")}</td>'
            f"<td>{len(source.objects)}</td>"
            f'<td class="code">{escape(", ".join(source.objects) or "—")}</td>'
            "</tr>"
            for source in result.sources
        )
        return self._table(("Source ID", "Path", "Objetos", "Objetos detectados"), rows)

    def _dependency_table(self, result: RepositoryAnalysisResult) -> str:
        if not result.graph.edges:
            return '<p class="empty">No se detectaron dependencias estáticas.</p>'
        rows = "".join(
            "<tr>"
            f'<td class="code">{escape(edge.source.name)}</td>'
            f'<td class="code">{escape(edge.target.name)}</td>'
            f'<td>{escape(edge.kind.value)}</td>'
            "</tr>"
            for edge in result.graph.edges
        )
        return self._table(("Source", "Target", "Tipo"), rows)

    def _key_objects_table(self, result: RepositoryAnalysisResult) -> str:
        ranked = [item for item in result.key_objects if item.dependent_count > 0][:20]
        if not ranked:
            return '<p class="empty">No hay objetos locales con dependientes estáticos.</p>'
        rows = "".join(
            "<tr>"
            f'<td class="code">{escape(item.name)}</td>'
            f"<td>{escape(item.object_type)}</td>"
            f"<td>{item.dependent_count}</td>"
            f"<td>{item.dependency_count}</td>"
            f'<td class="code">{escape(item.source_id)}</td>'
            "</tr>"
            for item in ranked
        )
        return self._table(("Objeto", "Tipo", "Dependientes", "Dependencias", "Fuente"), rows)

    def _cycles_panel(self, result: RepositoryAnalysisResult) -> str:
        if not result.cycles:
            return '<p class="empty">No se detectaron componentes circulares.</p>'
        items = "".join(
            f'<li><code>{escape(" ↔ ".join(cycle.members))}</code></li>'
            for cycle in result.cycles
        )
        return f'<div class="error-box">Se detectaron {len(result.cycles)} componente(s) circular(es).</div><ul class="clean">{items}</ul>'

    def _dead_objects_panel(self, result: RepositoryAnalysisResult) -> str:
        findings = result.dead_objects.findings
        warning = '<div class="warning-box"><strong>Revisión humana obligatoria.</strong> Un candidato nunca significa que sea seguro borrarlo; puede existir uso externo, dinámico u operativo no visible estáticamente.</div>'
        if not findings:
            return warning + '<p class="empty">No se detectaron candidatos.</p>'
        items = "".join(
            f'<li><code>{escape(", ".join(member.name for member in finding.members))}</code></li>'
            for finding in findings
        )
        return warning + f'<ul class="clean">{items}</ul>'

    def _findings_table(self, result: RepositoryAnalysisResult) -> str:
        if not result.static_analysis.findings:
            return '<p class="empty">No se generaron hallazgos.</p>'
        rows = "".join(
            "<tr>"
            f'<td><span class="badge {escape(finding.severity.value)}">{escape(finding.severity.value.upper())}</span></td>'
            f'<td class="code">{escape(finding.rule_id)}</td>'
            f"<td>{escape(finding.title)}</td>"
            f"<td>{escape(finding.message)}</td>"
            f'<td class="code">{escape(", ".join(finding.objects) or "—")}</td>'
            "</tr>"
            for finding in result.static_analysis.findings
        )
        return self._table(("Severidad", "Regla", "Título", "Detalle", "Objetos"), rows)

    def _uncertainty_panel(self, result: RepositoryAnalysisResult) -> str:
        names = [item.name for item in result.dynamic_sql_objects]
        if not names:
            return '<p class="empty">No se detectó evidencia de SQL dinámico en objetos locales.</p>'
        items = "".join(f'<li><code>{escape(name)}</code></li>' for name in names)
        return (
            '<div class="warning-box">El análisis es estático. Estas construcciones pueden ocultar dependencias que no pueden resolverse con certeza.</div>'
            f'<ul class="clean">{items}</ul>'
        )

    def _object_explorer(self, result: RepositoryAnalysisResult) -> str:
        if not result.objects:
            return '<p class="empty">No se detectaron objetos locales.</p>'
        rows = "".join(
            "<tr>"
            f'<td class="code">{escape(item.name)}</td>'
            f"<td>{escape(item.object_type)}</td>"
            f'<td class="code">{escape(item.source_id)}</td>'
            f'<td class="code">{escape(", ".join(item.dependencies) or "—")}</td>'
            f'<td class="code">{escape(", ".join(item.dependents) or "—")}</td>'
            f'<td>{"Sí" if item.dynamic_sql else "No"}</td>'
            "</tr>"
            for item in result.objects
        )
        return (
            '<input id="object-search" type="search" placeholder="Buscar objeto, tipo o fuente…" oninput="filterObjects()" aria-label="Buscar objetos">'
            + self._table(("Objeto", "Tipo", "Fuente", "Dependencias", "Dependientes", "SQL dinámico"), rows, table_id="object-table")
        )

    def _traceability_table(self, result: RepositoryAnalysisResult) -> str:
        rows = "".join(
            "<tr>"
            f'<td class="code">{escape(item.source_id)}</td>'
            f'<td class="code">{escape(item.name)}</td>'
            f"<td>{escape(item.object_type)}</td>"
            "</tr>"
            for item in sorted(result.objects, key=lambda value: (value.source_id.casefold(), value.name.casefold()))
        )
        if not rows:
            return '<p class="empty">No hay trazabilidad de objetos que mostrar.</p>'
        return self._table(("Fuente", "Objeto", "Tipo"), rows)

    @staticmethod
    def _table(headers: tuple[str, ...], rows: str, *, table_id: str | None = None) -> str:
        identifier = f' id="{escape(table_id)}"' if table_id else ""
        head = "".join(f"<th>{escape(header)}</th>" for header in headers)
        return f'<div class="table-wrap"><table{identifier}><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
