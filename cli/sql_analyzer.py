#!/usr/bin/env python3
import re, json
from pathlib import Path

PATTERNS = {
    "SELECT_STAR": r"SELECT\s+\*",
    "NOCOUNT": r"SET\s+NOCOUNT\s+ON",
    "CURSOR": r"\bCURSOR\b",
    "TEMP_TABLE": r"#\w+",
    "DYNAMIC_SQL": r"sp_executesql|EXEC\s*\(",
}

def analyze(file):
    text = Path(file).read_text(encoding="utf-8", errors="ignore")
    result = {"file": file, "findings": []}
    for name, pattern in PATTERNS.items():
        result["findings"].append({
            "rule": name,
            "matches": len(re.findall(pattern, text, flags=re.IGNORECASE))
        })
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("sql_file")
    args = ap.parse_args()
    analyze(args.sql_file)
