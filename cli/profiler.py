#!/usr/bin/env python3
import json
from pathlib import Path

TEMPLATE = {
  "timeline": [],
  "summary": {
    "elapsed_ms": None,
    "cpu_ms": None,
    "logical_reads": None
  }
}

def new_profile(output):
    Path(output).write_text(json.dumps(TEMPLATE, indent=2), encoding="utf-8")
    print(f"Created {output}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    args = ap.parse_args()
    new_profile(args.output)
