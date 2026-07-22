#!/usr/bin/env python3
import argparse
from pathlib import Path

def create_sprint(name):
    p=Path("sprints")/name
    p.mkdir(parents=True, exist_ok=True)
    (p/"README.md").write_text(f"# {name}\n",encoding="utf-8")
    print(f"Created {p}")

def create_handoff(name):
    p=Path("handoffs")/f"{name}.md"
    p.parent.mkdir(exist_ok=True)
    p.write_text(f"# Handoff {name}\n",encoding="utf-8")
    print(f"Created {p}")

ap=argparse.ArgumentParser(prog="sqlstudio")
sub=ap.add_subparsers(dest="cmd")
sp=sub.add_parser("new-sprint"); sp.add_argument("name")
ho=sub.add_parser("new-handoff"); ho.add_argument("name")
args=ap.parse_args()
if args.cmd=="new-sprint": create_sprint(args.name)
elif args.cmd=="new-handoff": create_handoff(args.name)
else: ap.print_help()
