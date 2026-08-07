#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
src_root_text = str(SRC_ROOT)
while src_root_text in sys.path:
    sys.path.remove(src_root_text)
sys.path.insert(0, src_root_text)

from sqlstudio import RepositoryEngine


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


def parse_sql_file(path: str) -> None:
    from sqlstudio import SQLParser

    parser = SQLParser()
    document = parser.parse(Path(path).read_text(encoding="utf-8", errors="ignore"))
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


def analyze_dependencies(
    paths: Iterable[str],
    *,
    output: str | None = None,
    recursive: bool = False,
    compact: bool = False,
    html: str | None = None,
) -> Path | None:
    """Analyze SQL files and print or write their dependency graph as JSON."""

    from sqlstudio.dependencies import DependencyAnalyzer, DependencyGraphSerializer

    files = _collect_sql_files(paths, recursive=recursive)
    sql_texts = [path.read_text(encoding="utf-8", errors="ignore") for path in files]
    graph = DependencyAnalyzer().analyze_many(sql_texts)
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
    html: str | None = None,
) -> Path | None:
    """Analyze SQL files and print or write cross-references as JSON."""

    from sqlstudio.cross_reference import (
        CrossReferenceAnalyzer,
        CrossReferenceSerializer,
    )

    files = _collect_sql_files(paths, recursive=recursive)
    sql_texts = [path.read_text(encoding="utf-8", errors="ignore") for path in files]
    references = CrossReferenceAnalyzer().analyze_many(sql_texts)
    indent = None if compact else 2

    if output:
        destination = CrossReferenceSerializer.write_json(
            references,
            output,
            indent=indent,
        )
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
    """Analyze SQL files and print or write an impact report as JSON."""

    from sqlstudio.impact_analysis import ImpactAnalyzer, ImpactResultSerializer, ImpactReportExporter

    files = _collect_sql_files(paths, recursive=recursive)
    sql_texts = [path.read_text(encoding="utf-8", errors="ignore") for path in files]
    result = ImpactAnalyzer().analyze_many(sql_texts, root_object)
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
    """Detect circular SQL dependencies and emit deterministic JSON."""

    from sqlstudio.circular_dependencies import (
        CircularDependencyAnalyzer,
        CircularDependencySerializer,
    )

    files = _collect_sql_files(paths, recursive=recursive)
    sql_texts = [path.read_text(encoding="utf-8", errors="ignore") for path in files]
    cycles = CircularDependencyAnalyzer().analyze_many(sql_texts)
    indent = None if compact else 2

    if output:
        destination = CircularDependencySerializer.write_json(
            cycles,
            output,
            indent=indent,
        )
        print(destination)
        return destination

    print(CircularDependencySerializer.to_json(cycles, indent=indent))
    return None


def build_parser():
    import argparse

    ap = argparse.ArgumentParser(prog="sqlstudio")
    sub = ap.add_subparsers(dest="cmd")

    sp = sub.add_parser("new-sprint")
    sp.add_argument("name")

    ho = sub.add_parser("new-handoff")
    ho.add_argument("name")

    sc = sub.add_parser("scan")
    sc.add_argument("folder")

    ps = sub.add_parser("parse")
    ps.add_argument("file")

    dep = sub.add_parser(
        "dependencies",
        help="Analyze SQL object dependencies and emit a JSON graph",
    )
    dep.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    dep.add_argument(
        "-o",
        "--output",
        help="Write JSON to this file instead of stdout",
    )
    dep.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search supplied directories recursively",
    )
    dep.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without indentation",
    )

    xref = sub.add_parser(
        "cross-references",
        help="Analyze SQL cross-references and emit JSON",
    )
    xref.add_argument("paths", nargs="+", help="SQL files or directories to analyze")
    xref.add_argument(
        "-o",
        "--output",
        help="Write JSON to this file instead of stdout",
    )
    xref.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search supplied directories recursively",
    )
    xref.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without indentation",
    )

    impact = sub.add_parser(
        "impact",
        help="Analyze transitive SQL dependencies from a selected object",
    )
    impact.add_argument(
        "root_object",
        help="Qualified SQL object used as the analysis root",
    )
    impact.add_argument(
        "paths",
        nargs="+",
        help="SQL files or directories to analyze",
    )
    impact.add_argument("-o", "--output", help="Write JSON to this file instead of stdout")
    impact.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search supplied directories recursively",
    )
    impact.add_argument("--html", help="Write HTML report to this file")
    impact.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without indentation",
    )

    cycles = sub.add_parser(
        "circular-dependencies",
        help="Detect circular SQL dependency components and emit JSON",
    )
    cycles.add_argument(
        "paths",
        nargs="+",
        help="SQL files or directories to analyze",
    )
    cycles.add_argument(
        "-o",
        "--output",
        help="Write JSON to this file instead of stdout",
    )
    cycles.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search supplied directories recursively",
    )
    cycles.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without indentation",
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
            analyze_dependencies(
                args.paths,
                output=args.output,
                recursive=args.recursive,
                compact=args.compact,
            )
        elif args.cmd == "cross-references":
            analyze_cross_references(
                args.paths,
                output=args.output,
                recursive=args.recursive,
                compact=args.compact,
            )
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
            analyze_circular_dependencies(
                args.paths,
                output=args.output,
                recursive=args.recursive,
                compact=args.compact,
            )
        else:
            ap.print_help()
            return 0
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())