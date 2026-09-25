"""Minimum documentation presence checks; never scan sensitive dotfiles."""
from __future__ import annotations

from pathlib import Path

from .common import Finding, finding


def analyze_documentation(root: Path) -> list[Finding]:
    if any((root / name).is_file() and not (root / name).is_symlink()
           for name in ("README.md", "README.rst", "README.txt", "README")):
        return []
    return [finding(
        category="documentation", severity="low", title="README missing",
        file=".", line=None,
        description="The repository does not contain a root-level README.",
        recommendation="Add setup, installation, usage, test commands, and limitations to a README.",
    )]
