"""Python AST rules: broad exception handling, long functions, syntax problems."""
from __future__ import annotations

import ast
from pathlib import Path

from .common import Finding, finding, safe_source_lines

LONG_FUNCTION_LINES = 45


def analyze_quality(files: list[Path], root: Path) -> list[Finding]:
    results: list[Finding] = []
    for path in files:
        if path.suffix.lower() != ".py":
            continue
        lines = safe_source_lines(path)
        if lines is None:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse("\n".join(lines), filename=relative)
        except SyntaxError as error:
            results.append(finding(
                category="maintainability", severity="medium",
                title="Python syntax error", file=relative, line=error.lineno,
                description="This file contains Python syntax that cannot be parsed.",
                recommendation="Resolve the syntax error before running or deploying this module.",
            ))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    results.append(finding(
                        category="error_handling", severity="medium",
                        title="Bare except clause", file=relative, line=node.lineno,
                        description="A bare except catches system-exiting exceptions as well as expected errors.",
                        recommendation="Catch only the specific exception types this code expects.",
                    ))
                elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    results.append(finding(
                        category="error_handling", severity="medium",
                        title="Broad exception handler", file=relative, line=node.lineno,
                        description="This handler catches Exception broadly.",
                        recommendation="Catch more specific exception types where possible.",
                    ))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", None)
                if end is not None and end - node.lineno + 1 > LONG_FUNCTION_LINES:
                    results.append(finding(
                        category="maintainability", severity="low",
                        title="Long function", file=relative, line=node.lineno,
                        description=f"Function '{node.name}' spans {end - node.lineno + 1} lines.",
                        recommendation="Consider extracting logically independent operations into smaller functions.",
                    ))
    return results
