"""Conservative, offline detection of potentially hardcoded credentials.

This is a demonstration heuristic, NOT a security audit or secret validator.
Never include credential values or matching source lines in findings or logs.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import Finding, finding, safe_source_lines

# Match assignments to credential-looking variable names in Python, JS and TS.
# Deliberately avoid parsing arbitrary strings or logging matched secrets.
ASSIGNMENT = re.compile(
    r'''^\s*(?:(?:export\s+)?(?:const|let|var)\s+)?'''
    r'''(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*str\s*)?=\s*'''
    r'''(?P<quote>["'`])(?P<value>[^"'`]{6,256})(?P=quote)'''
)
CREDENTIAL_NAME = re.compile(
    r"(?:api[_-]?key|secret|password|passwd|private[_-]?key|access[_-]?token|auth[_-]?token)",
    re.IGNORECASE,
)
PLACEHOLDERS = frozenset({
    "changeme", "change_me", "placeholder", "your_key_here", "your_api_key",
    "example", "password", "not_set", "replace_me", "none",
})
SOURCE_SUFFIXES = frozenset({".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"})


def analyze_security(files: list[Path], root: Path) -> list[Finding]:
    results: list[Finding] = []
    for path in files:
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        lines = safe_source_lines(path)
        if lines is None:
            continue
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(lines, 1):
            if line.lstrip().startswith(("#", "//", "*")):
                continue
            match = ASSIGNMENT.match(line)
            if match is None or CREDENTIAL_NAME.search(match.group("name")) is None:
                continue
            value = match.group("value").strip().lower()
            if value in PLACEHOLDERS or value.startswith(("${", "<", "{{")):
                continue
            results.append(finding(
                category="security", severity="high",
                title="Potential hardcoded credential", file=relative, line=number,
                description="A credential-like variable appears to contain a string literal.",
                recommendation="Use environment configuration or a secrets manager; rotate any real exposed credential.",
            ))
    return results
