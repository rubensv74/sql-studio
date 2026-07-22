#!/usr/bin/env python3
import argparse, json, datetime
from pathlib import Path

def benchmark(project, elapsed_ms, cpu_ms=None, logical_reads=None):
    out = {
        "timestamp": datetime.datetime.utcnow().isoformat()+"Z",
        "project": project,
        "elapsed_ms": elapsed_ms,
        "cpu_ms": cpu_ms,
        "logical_reads": logical_reads
    }
    path = Path("benchmarks")
    path.mkdir(exist_ok=True)
    file = path / f"{project}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(file)

ap=argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("elapsed_ms", type=int)
ap.add_argument("--cpu_ms", type=int)
ap.add_argument("--logical_reads", type=int)
args=ap.parse_args()
benchmark(args.project,args.elapsed_ms,args.cpu_ms,args.logical_reads)
