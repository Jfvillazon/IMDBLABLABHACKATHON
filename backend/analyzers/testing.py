"""Detect whether Python and JavaScript/TypeScript code has conventional tests."""
from __future__ import annotations

from pathlib import Path

from .common import Finding, finding

PYTHON_EXTENSIONS = frozenset({".py"})
JS_EXTENSIONS = frozenset({".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"})


def _is_test(path: Path) -> bool:
    name = path.name.lower()
    return (
        name.startswith("test_") or name.endswith("_test.py") or
        ".test." in name or ".spec." in name or
        "__tests__" in {part.lower() for part in path.parts}
    )


def analyze_testing(files: list[Path], root: Path) -> list[Finding]:
    source = [path for path in files
              if path.suffix.lower() in (PYTHON_EXTENSIONS | JS_EXTENSIONS)
              and not _is_test(path)]
    if not source:
        return []
    tests = [path for path in files if _is_test(path)
             and path.suffix.lower() in (PYTHON_EXTENSIONS | JS_EXTENSIONS)]
    if tests:
        return []
    return [finding(
        category="testing", severity="high", title="No automated tests detected",
        file=".", line=None,
        description="Source code was found but no conventionally named test files were detected.",
        recommendation="Add automated tests for critical workflows and commit them with the source.",
    )]
