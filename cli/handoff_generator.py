#!/usr/bin/env python3
from pathlib import Path
import json, datetime

def generate(project_path, output):
    project=Path(project_path)
    data={
        "generated":datetime.datetime.utcnow().isoformat()+"Z",
        "project":project.name,
        "sql_files":[str(p.relative_to(project)) for p in project.rglob("*.sql")],
        "md_files":[str(p.relative_to(project)) for p in project.rglob("*.md")]
    }
    Path(output).write_text(json.dumps(data,indent=2),encoding="utf-8")
    print(output)

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("output")
    a=ap.parse_args()
    generate(a.project,a.output)
