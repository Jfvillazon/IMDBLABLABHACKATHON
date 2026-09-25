"""Shared safety limits and a consistent finding representation.

Never include source lines or matched credential values in API findings.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

Severity = Literal["high", "medium", "low"]

MAX_SOURCE_BYTES = 512 * 1024
MAX_LINES_PER_FILE = 8_000


class Finding(TypedDict):
    id: str
    category: str
    severity: Severity
    title: str
    file: str
    line: int | None
    description: str
    recommendation: str


def finding(*, category: str, severity: Severity, title: str,
            file: str, line: int | None, description: str,
            recommendation: str) -> Finding:
    return {
        "id": "",  # Assigned in a deterministic order by the engine.
        "category": category,
        "severity": severity,
        "title": title,
        "file": file,
        "line": line,
        "description": description,
        "recommendation": recommendation,
    }


def safe_source_lines(path: Path) -> list[str] | None:
    """Read a bounded, regular, nonsymlink source file; skip unreadable data.

    This is deliberately *static* analysis: file content is never executed.
    """
    try:
        if path.is_symlink() or not path.is_file():
            return None
        if path.stat().st_size > MAX_SOURCE_BYTES:
            return None
        with path.open("r", encoding="utf-8", errors="replace") as stream:
            lines: list[str] = []
            for index, line in enumerate(stream):
                if index >= MAX_LINES_PER_FILE:
                    return None  # Avoid false syntax errors on truncated modules.
                lines.append(line.rstrip("\r\n"))
            return lines
    except (OSError, UnicodeError):
        return None
