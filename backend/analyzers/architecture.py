"""Lightweight, deterministic repository structure inspection."""
from __future__ import annotations

from pathlib import Path

from .common import Finding, finding

ENTRY_POINT_FILENAMES = frozenset({
    "main.py", "app.py", "manage.py", "server.py", "index.js",
    "index.ts", "main.js", "main.ts", "App.jsx", "App.tsx",
    "package.json", "Dockerfile",
})


def summarize_architecture(root: Path, files: list[Path]) -> dict[str, list[str]]:
    """Metadata for internal/report use; does not change the frozen API contract."""
    return {
        "top_level_directories": sorted({
            path.relative_to(root).parts[0]
            for path in files if len(path.relative_to(root).parts) > 1
        }),
        "entry_points": sorted({
            path.relative_to(root).as_posix()
            for path in files if path.name in ENTRY_POINT_FILENAMES
        }),
    }


def analyze_architecture(root: Path, files: list[Path]) -> list[Finding]:
    """Flag a very large, completely flat source tree as a maintainability hint.

    No architectural patterns are inferred from insufficient static evidence.
    """
    if len(files) < 15:
        return []
    all_top_level = all(len(path.relative_to(root).parts) == 1 for path in files)
    if not all_top_level:
        return []
    return [finding(
        category="maintainability", severity="low",
        title="Large flat source directory", file=".", line=None,
        description="Many source files share one directory, making navigation harder.",
        recommendation="Consider grouping related source files into focused packages or modules.",
    )]
