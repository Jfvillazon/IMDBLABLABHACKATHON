"""Explainable severity-based scoring frozen by the hackathon execution plan."""
from __future__ import annotations

from .common import Finding

DEDUCTIONS = {"high": 10, "medium": 5, "low": 2}


def calculate_health_score(findings: list[Finding]) -> int:
    return max(0, min(100, 100 - sum(
        DEDUCTIONS.get(item["severity"], 0) for item in findings
    )))
