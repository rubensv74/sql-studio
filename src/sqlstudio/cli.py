from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

from ._version import __version__
from .repository import RepositoryEngine
from .source import SqlSource


def create_sprint(name: str) -> None:
    p = Path("sprints") / name
    p.mkdir(parents=True, exist_ok=True)
    (p / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    print(f"Created {p}")


def create_handoff(name: str) -> None:
    p = Path("handoffs") / f"{name}.md"
    p.parent.mkdir(exist_ok=True)
    p.write_text(f"# Handoff {name}\n", encoding="utf-8")
    print(f"Created {p}")


def scan_repository(folder: str) -> None:
    engine = RepositoryEngine(folder)
    print(engine.to_json(folder))


def _source_id_for_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _sql_source_from_path(path: Path) -> SqlSource:
    return SqlSource.from_path(path, source_id=_source_id_for_path(path))


def parse_sql_file(path: str) -> None:
    from .parser import SQLParser

    source_path = Path(path)
    parser = SQLParser()
    document = parser.parse_source(_sql_source_from_path(source_path))
    payload = {
        "sql_text": document.sql_text,
        "objects": [
            {
                "name": obj.name,
                "schema": obj.schema,
                "object_type": obj.object_type,
                "parameters": [
                    {
                        "name": param.name,
                        "datatype": param.datatype,
                        "default_value": param.default_value,
                        "output": param.output,
                    }
                    for param in obj.parameters
                ],
                "variables": [
                    {"name": var.name, "value": var.value}
                    for var in obj.variables
                ],
                "references": [
                    {
                        "name": ref.name,
                        "schema": ref.schema,
                        "database": ref.database,
                        "kind": ref.kind,
                    }
                    for ref in obj.references
                ],
                "temporary_tables": obj.temporary_tables,
                "dynamic_sql": obj.dynamic_sql,
            }
            for obj in document.objects
        ],
    }
    print(json.dumps(payload, indent=2))


def _collect_sql_files(paths: Iterable[str], recursive: bool = False) -> list[Path]:
    """Resolve input files and directories into a stable list of SQL files."""

    resolved: dict[str, Path] = {}
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"Input path does not exist: {path}")

        if path.is_file():
            if path.suffix.casefold() != ".sql":
                raise ValueError(f"Input file is not a .sql file: {path}")
            resolved[str(path.resolve()).casefold()] = path
            continue

        pattern = "**/*.sql" if recursive else "*.sql"
        for sql_file in path.glob(pattern):
            if sql_file.is_file():
                resolved[str(sql_file.resolve()).casefold()] = sql_file

    files = sorted(resolved.values(), key=lambda item: str(item).casefold())
    if not files:
        raise FileNotFoundError("No SQL files were found in the supplied input paths")
    return files


def _read_sql_sources(paths: Iterable[str], *, recursive: bool) -> list[SqlSource]:
    return [
        _sql_source_from_path(path)
        for path in _collect_sql_files(paths, recursive=recursive)
    ]


def analyze_dependencies(
    paths: Iterable[str],
    *,
    output: str | None = None,
    recursive: bool = False,
    compact: bool = False,
) -> Path | None:
    from .dependencies import DependencyAnalyzer, DependencyGraphSerializer

    graph = DependencyAnalyzer().analyze_sources(
        _read_sql_sources(paths, recursive=recursive)
    )
    indent = None if compact else 2
    if output:
        destination = DependencyGraphSerializer.write_json(graph, output, indent=indent)
        print(destination)
        return destination
    print(DependencyGraphSerializer.to_json(graph, indent=indent))
    return None


def analyze_cross_references(
    paths: Iterable[str],
    *,
    output: str | None = None,
    recursive: bool = False,
    compact: bool = False,
) -> Path | None:
    from .cross_reference import CrossReferenceAnalyzer, CrossReferenceSerializer

    references = CrossReferenceAnalyzer().analyze_sources(
        _read_sql_sources(paths, recursive=recursive)
    )
    indent = None if compact else 2
    if output:
        destination = CrossReferenceSerializer.write_json(references, output, indent=indent)
        print(destination)
        return destination
    print(CrossReferenceSerializer.to_json(references, indent=indent))
    return None


def analyze_impact(
    paths: Iterable[str],
    root_object: str,
    *,
    output: str | None = None,
    recursive: bool = False,
    compact: bool = False,
    html: str | None = None,
) -> Path | None:
    from .impact_analysis import ImpactAnalyzer, ImpactReportExporter, ImpactResultSerializer

    result = ImpactAnalyzer().analyze_sources(
        _read_sql_sources(paths, recursive=recursive), root_object
    )
    indent = None if compact else 2
    if html:
        destination = ImpactReportExporter().export(result, html)
        print(destination)
        return destination

    payload = ImpactResultSerializer.to_json(result, indent=indent)
    if output:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(payload, encoding="utf-8")
        print(destination)
        return destination
    print(payload)
    return None


def analyze_circular_dependencies(
    paths: Iterable[str],
    *,
    output: str | None = None,
    recursive: bool = False,
    compact: bool = False,
) -> Path | None:
    from .circular_dependencies import CircularDependencyAnalyzer, CircularDependencySerializer

    cycles = CircularDependencyAnalyzer().analyze_sources(
        _read_sql_sources(paths, recursive=recursive)
    )
    indent = None if compact else 2
    if output:
        destination = CircularDependencySerializer.write_json(cycles, output, indent=indent)
        print(destination)
        return destination
    print(CircularDependencySerializer.to_json(cycles, indent=indent))
    return None


def analyze_dead_objects(
    paths: Iterable[str],
    *,
    output: str | None = None,
    recursive: bool = False,
    compact: bool = False,
    entry_points: Iterable[str] = (),
) -> Path | None:
    from .dead_objects import DeadObjectAnalyzer, DeadObjectSerializer

    result = DeadObjectAnalyzer().analyze_sources(
        _read_sql_sources(paths, recursive=recursive),
        entry_points=entry_points,
    )
    indent = None if compact else 2
    if output:
        destination = DeadObjectSerializer.write_json(result, output, indent=indent)
        print(destination)
        return destination
    print(DeadObjectSerializer.to_json(result, indent=indent))
    return None


def analyze_static_rules(
    paths: Iterable[str],
    *,
    output: str | None = None,
    recursive: bool = False,
    compact: bool = False,
    entry_points: Iterable[str] = (),
    rule_ids: Iterable[str] = (),
):
    """Execute the consolidated static-analysis rule engine and emit JSON."""

    from .rules import StaticAnalysisAnalyzer, StaticAnalysisSerializer

    result = StaticAnalysisAnalyzer().analyze_sources(
        _read_sql_sources(paths, recursive=recursive),
        entry_points=entry_points,
        rule_ids=rule_ids,
    )
    indent = None if compact else 2
    if output:
        destination = StaticAnalysisSerializer.write_json(result, output, indent=indent)
        print(destination)
    else:
        print(StaticAnalysisSerializer.to_json(result, indent=indent))
    return result


def build_parser():
    import argparse

    ap = argparse.ArgumentParser(prog="sqlstudio")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="cmd")

    sp = sub.add_parser("new-sprint")
    sp.add_argument("name")

    ho = sub.add_parser("new-handoff")
    ho.add_argument("name")

    sc = sub.add_parser("scan")
    sc.add_argument("folder")

    ps = sub.add_parser("parse")
    ps.add_argument("file")

    dep = sub.add_parser("dependencies", help="Analyze SQL object dependencies and emit a JSON graph")
    dep.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    dep.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    dep.add_argument("-r", "--recursive", action="store_true", help="Search supplied directories recursively")
    dep.add_argument("--compact", action="store_true", help="Emit compact JSON without indentation")

    xref = sub.add_parser("cross-references", help="Analyze SQL cross-references and emit JSON")
    xref.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    xref.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    xref.add_argument("-r", "--recursive", action="store_true", help="Search supplied directories recursively")
    xref.add_argument("--compact", action="store_true", help="Emit compact JSON without indentation")

    impact = sub.add_parser("impact", help="Analyze transitive change impact from a selected object")
    impact.add_argument("root_object", help="Qualified SQL object used as the analysis root")
    impact.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    impact.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    impact.add_argument("-r", "--recursive", action="store_true", help="Search supplied directories recursively")
    impact.add_argument("--html", help="Write HTML report to this file")
    impact.add_argument("--compact", action="store_true", help="Emit compact JSON without indentation")

    cycles = sub.add_parser("circular-dependencies", help="Detect circular SQL dependency components and emit JSON")
    cycles.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    cycles.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    cycles.add_argument("-r", "--recursive", action="store_true", help="Search supplied directories recursively")
    cycles.add_argument("--compact", action="store_true", help="Emit compact JSON without indentation")

    dead = sub.add_parser(
        "dead-objects",
        help="Find unreferenced SQL object candidates that require human review",
    )
    dead.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    dead.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    dead.add_argument("-r", "--recursive", action="store_true", help="Search supplied directories recursively")
    dead.add_argument("--compact", action="store_true", help="Emit compact JSON without indentation")
    dead.add_argument(
        "--entry-point",
        action="append",
        default=[],
        metavar="OBJECT",
        help="Qualified SQL object known to be invoked externally; repeat as needed",
    )

    rules = sub.add_parser(
        "analyze",
        help="Run consolidated static-analysis rules and emit normalized findings",
    )
    rules.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    rules.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    rules.add_argument("-r", "--recursive", action="store_true", help="Search supplied directories recursively")
    rules.add_argument("--compact", action="store_true", help="Emit compact JSON without indentation")
    rules.add_argument(
        "--entry-point",
        action="append",
        default=[],
        metavar="OBJECT",
        help="Known externally invoked SQL object used by rules such as SQL002",
    )
    rules.add_argument(
        "--rule",
        action="append",
        default=[],
        metavar="RULE_ID",
        help="Run only the selected rule id; repeat as needed (default: all rules)",
    )
    rules.add_argument(
        "--fail-on",
        choices=("info", "warning", "error"),
        metavar="SEVERITY",
        help="Return exit code 2 when a finding at or above this severity exists",
    )

    return ap


def main() -> int:
    ap = build_parser()
    args = ap.parse_args()

    try:
        if args.cmd == "new-sprint":
            create_sprint(args.name)
        elif args.cmd == "new-handoff":
            create_handoff(args.name)
        elif args.cmd == "scan":
            scan_repository(args.folder)
        elif args.cmd == "parse":
            parse_sql_file(args.file)
        elif args.cmd == "dependencies":
            analyze_dependencies(args.paths, output=args.output, recursive=args.recursive, compact=args.compact)
        elif args.cmd == "cross-references":
            analyze_cross_references(args.paths, output=args.output, recursive=args.recursive, compact=args.compact)
        elif args.cmd == "impact":
            analyze_impact(
                args.paths,
                args.root_object,
                output=args.output,
                recursive=args.recursive,
                compact=args.compact,
                html=args.html,
            )
        elif args.cmd == "circular-dependencies":
            analyze_circular_dependencies(args.paths, output=args.output, recursive=args.recursive, compact=args.compact)
        elif args.cmd == "dead-objects":
            analyze_dead_objects(
                args.paths,
                output=args.output,
                recursive=args.recursive,
                compact=args.compact,
                entry_points=args.entry_point,
            )
        elif args.cmd == "analyze":
            result = analyze_static_rules(
                args.paths,
                output=args.output,
                recursive=args.recursive,
                compact=args.compact,
                entry_points=args.entry_point,
                rule_ids=args.rule,
            )
            if args.fail_on and result.has_at_or_above(args.fail_on):
                return 2
        else:
            ap.print_help()
            return 0
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
