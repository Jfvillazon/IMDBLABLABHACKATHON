"""Measure this analyzer's runtime; does not claim a manual-work baseline.

Usage: python scripts/benchmark_analysis.py sample_repo
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

# When run as a script from the project root, ensure package imports resolve.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.analyzers.engine import analyze_repository  # noqa: E402


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sample_repo")
    elapsed = []
    result = None
    for _ in range(5):
        started = time.perf_counter()
        result = analyze_repository(path)
        elapsed.append(time.perf_counter() - started)
    print(json.dumps({
        "repository": result["repository"],
        "files_analyzed": result["files_analyzed"],
        "findings": len(result["findings"]),
        "median_runtime_seconds": round(statistics.median(elapsed), 5),
        "runs": len(elapsed),
        "note": "Automated runtime only. Measure manual review separately before comparing.",
    }, indent=2))


if __name__ == "__main__":
    main()
