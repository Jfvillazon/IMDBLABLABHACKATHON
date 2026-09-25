"""Print basic architecture metadata without changing the /api/analyze JSON.

Usage: python scripts/inspect_architecture.py sample_repo
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.analyzers.engine import inspect_repository_structure  # noqa: E402


def main() -> None:
    selected = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("sample_repo")
    root = selected if selected.is_absolute() else PROJECT_ROOT / selected
    print(json.dumps(inspect_repository_structure(root), indent=2))


if __name__ == "__main__":
    main()