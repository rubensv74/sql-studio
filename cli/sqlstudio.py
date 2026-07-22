#!/usr/bin/env python3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio import RepositoryEngine


def create_sprint(name):
    p = Path("sprints") / name
    p.mkdir(parents=True, exist_ok=True)
    (p / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    print(f"Created {p}")


def create_handoff(name):
    p = Path("handoffs") / f"{name}.md"
    p.parent.mkdir(exist_ok=True)
    p.write_text(f"# Handoff {name}\n", encoding="utf-8")
    print(f"Created {p}")


def scan_repository(folder):
    engine = RepositoryEngine(folder)
    print(engine.to_json(folder))


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="sqlstudio")
    sub = ap.add_subparsers(dest="cmd")
    sp = sub.add_parser("new-sprint")
    sp.add_argument("name")
    ho = sub.add_parser("new-handoff")
    ho.add_argument("name")
    sc = sub.add_parser("scan")
    sc.add_argument("folder")
    args = ap.parse_args()

    try:
        if args.cmd == "new-sprint":
            create_sprint(args.name)
        elif args.cmd == "new-handoff":
            create_handoff(args.name)
        elif args.cmd == "scan":
            scan_repository(args.folder)
        else:
            ap.print_help()
            return 0
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
