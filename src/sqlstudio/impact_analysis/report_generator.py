from __future__ import annotations

from html import escape
from typing import Iterable, Optional

from .models import ImpactNode, ImpactResult


class ImpactReportGenerator:
    """Generate a self-contained HTML impact-analysis report."""

    def generate(
        self,
        result: ImpactResult,
        *,
        direct_objects: Optional[Iterable[str]] = None,
    ) -> str:
        root = result.root_object
        impacted = self._unique_without_root(result.impacted_objects, root)
        direct = self._ordered_subset(direct_objects or (), impacted)
        direct_set = {item.casefold() for item in direct}
        indirect = [item for item in impacted if item.casefold() not in direct_set]
        tree = getattr(result, "tree", None) or self._flat_tree(root, impacted)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Impact Report · {escape(root)}</title>
<style>
:root {{
  color-scheme: light;
  --background: #f5f7fa;
  --surface: #ffffff;
  --border: #e5e7eb;
  --text: #0f172a;
  --muted: #64748b;
  --primary: #1677ff;
  --primary-soft: #eaf3ff;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--background);
  color: var(--text);
  font-family: Inter, "Segoe UI", Arial, sans-serif;
}}
main {{ max-width: 1080px; margin: 0 auto; padding: 40px 24px 56px; }}
header {{ margin-bottom: 24px; }}
h1 {{ margin: 0 0 8px; font-size: 30px; }}
.subtitle {{ margin: 0; color: var(--muted); }}
.root-card, .panel, .metric {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
}}
.root-card {{ padding: 20px; margin-bottom: 20px; }}
.label {{ color: var(--muted); font-size: 13px; font-weight: 600; text-transform: uppercase; }}
.object-name {{ margin-top: 8px; font-family: Consolas, monospace; font-size: 18px; word-break: break-word; }}
.metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }}
.metric {{ padding: 18px; }}
.metric strong {{ display: block; margin-top: 6px; font-size: 28px; }}
.grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; margin-bottom: 20px; }}
.panel {{ padding: 20px; }}
.panel h2 {{ margin: 0 0 16px; font-size: 18px; }}
ul {{ margin: 0; padding: 0; list-style: none; }}
.dependency-list li {{
  position: relative;
  margin: 0 0 10px 14px;
  padding: 11px 12px 11px 18px;
  border-left: 2px solid var(--primary);
  border-radius: 0 8px 8px 0;
  background: var(--primary-soft);
  font-family: Consolas, monospace;
  word-break: break-word;
}}
.tree {{ overflow-x: auto; }}
.tree ul {{ margin-left: 18px; padding-left: 14px; border-left: 1px solid var(--border); }}
.tree li {{ margin: 8px 0; font-family: Consolas, monospace; }}
.tree-node {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 7px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  cursor: default;
}}
.tree-node.expandable {{ cursor: pointer; }}
.tree-node.expandable::before {{ content: "▾"; color: var(--primary); }}
.tree-node.expandable.collapsed::before {{ content: "▸"; }}
.empty {{ margin: 0; color: var(--muted); }}
@media (max-width: 720px) {{
  .metrics, .grid {{ grid-template-columns: 1fr; }}
  main {{ padding: 24px 16px 40px; }}
}}
</style>
</head>
<body>
<main>
<header>
  <h1>Informe de impacto</h1>
  <p class="subtitle">Dependencias potencialmente afectadas por un cambio.</p>
</header>
<section class="root-card">
  <div class="label">Objeto raíz</div>
  <div class="object-name">{escape(root)}</div>
</section>
<section class="metrics" aria-label="Resumen de impacto">
  {self._metric("Impacto total", len(impacted))}
  {self._metric("Dependencias directas", len(direct))}
  {self._metric("Dependencias indirectas", len(indirect))}
</section>
<section class="grid">
  {self._panel("Dependencias directas", direct)}
  {self._panel("Dependencias indirectas", indirect)}
</section>
{self._tree_panel(tree)}
</main>
{self._tree_script()}
</body>
</html>"""

    @staticmethod
    def _unique_without_root(objects: Iterable[str], root: str) -> list[str]:
        unique: list[str] = []
        seen = {root.casefold()}
        for item in objects:
            key = item.casefold()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    @staticmethod
    def _ordered_subset(objects: Iterable[str], impacted: list[str]) -> list[str]:
        allowed = {item.casefold(): item for item in impacted}
        selected: list[str] = []
        seen: set[str] = set()
        for item in objects:
            key = item.casefold()
            if key in allowed and key not in seen:
                seen.add(key)
                selected.append(allowed[key])
        return selected

    @staticmethod
    def _flat_tree(root: str, objects: Iterable[str]) -> ImpactNode:
        return ImpactNode(name=root, children=[ImpactNode(name=item) for item in objects])

    def _tree_panel(self, tree: ImpactNode) -> str:
        return (
            '<section class="panel tree">'
            '<h2>Árbol de dependencias</h2>'
            f'<ul>{self._render_tree(tree, "impact-tree")}</ul>'
            '</section>'
        )

    def _render_tree(self, node: ImpactNode, node_id: str) -> str:
        children = list(node.children or [])
        safe_name = escape(str(node.name))

        if not children:
            return f'<li><span class="tree-node">{safe_name}</span></li>'

        child_items = "".join(
            self._render_tree(child, f"{node_id}-{index}")
            for index, child in enumerate(children)
        )
        return (
            '<li>'
            f'<button type="button" class="tree-node expandable" '
            f'aria-expanded="true" aria-controls="{node_id}" '
            f'onclick="toggleImpactNode(this, \'{node_id}\')">{safe_name}</button>'
            f'<ul id="{node_id}">{child_items}</ul>'
            '</li>'
        )

    @staticmethod
    def _tree_script() -> str:
        return """<script>
function toggleImpactNode(button, id) {
  const branch = document.getElementById(id);
  if (!branch) return;
  const collapsed = branch.hidden === true;
  branch.hidden = !collapsed;
  button.setAttribute('aria-expanded', collapsed ? 'true' : 'false');
  button.classList.toggle('collapsed', !collapsed);
}
</script>"""

    @staticmethod
    def _metric(label: str, value: int) -> str:
        return (
            '<article class="metric">'
            f'<span class="label">{escape(label)}</span>'
            f'<strong>{value}</strong>'
            '</article>'
        )

    @staticmethod
    def _panel(title: str, objects: list[str]) -> str:
        if objects:
            content = "".join(f"<li>{escape(item)}</li>" for item in objects)
            body = f'<ul class="dependency-list">{content}</ul>'
        else:
            body = '<p class="empty">No hay objetos en esta categoría.</p>'
        return f'<article class="panel"><h2>{escape(title)}</h2>{body}</article>'
