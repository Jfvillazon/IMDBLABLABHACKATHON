"""Member 2's end-to-end orchestration; API and CLI share this engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .architecture import analyze_architecture, summarize_architecture
from .documentation import analyze_documentation
from .health import calculate_health_score
from .quality import analyze_quality
from .repository import scan_repository
from .security import analyze_security
from .testing import analyze_testing

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def analyze_repository(repo_path: str | Path) -> dict[str, Any]:
    scan = scan_repository(repo_path)
    root, files = scan["root"], scan["files"]
    findings = [
        *analyze_architecture(root, files),
        *analyze_quality(files, root),
        *analyze_testing(files, root),
        *analyze_security(files, root),
        *analyze_documentation(root),
    ]
    findings.sort(key=lambda item: (
        SEVERITY_ORDER[item["severity"]], item["category"], item["file"],
        item["line"] if item["line"] is not None else 0, item["title"],
    ))
    for index, item in enumerate(findings, 1):
        item["id"] = f"F{index:03d}"
    return {
        "repository": scan["repository"],
        "files_analyzed": scan["files_analyzed"],
        "languages": scan["languages"],
        "health_score": calculate_health_score(findings),
        "findings": findings,
    }


def inspect_repository_structure(repo_path: str | Path) -> dict[str, Any]:
    """Expose architecture metadata for reports without changing /api/analyze.

    The frontend's approved analysis contract has exactly five top-level
    fields. An optional CLI report can use this function now; a future UI
    integration requires agreement with Member 3.
    """
    scan = scan_repository(repo_path)
    return {
        "repository": scan["repository"],
        **summarize_architecture(scan["root"], scan["files"]),
    }
