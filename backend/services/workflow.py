"""
Engineering Workflow Orchestration — RepoMedic.

Public interface:
    run_engineering_workflow(
        issue: str,
        repository_path: str,
        test_path: str | None = None,
    ) -> EngineeringReport

Execution sequence:
  1. Call investigate_issue(issue, repository_path) → InvestigateResponse
  2. Call run_validation(resolved_test_path)         → ValidateResponse
  3. Call build_engineering_report(investigation, validation) → EngineeringReport
  4. Return the EngineeringReport

This module:
  - does NOT duplicate investigation, validation, report, parsing, or
    recommendation logic
  - does NOT add shell commands, shell=True, or subprocess calls
  - does NOT modify any repository file
  - does NOT apply repairs automatically
  - does NOT invent test results or fabricate investigation claims
  - is deterministic and suitable for the controlled hackathon sample repo
"""

from __future__ import annotations

from backend.models.schemas import EngineeringReport
from backend.services.investigation import investigate_issue
from backend.services.report import build_engineering_report
from backend.services.validation import run_validation


def run_engineering_workflow(
    issue: str,
    repository_path: str,
    test_path: str | None = None,
) -> EngineeringReport:
    """
    Orchestrate the full investigation → validation → engineering-report pipeline.

    Parameters
    ----------
    issue:
        Developer issue description.  Passed verbatim to investigate_issue.
        Must be a non-empty string; ValueError is raised when it is empty.
    repository_path:
        Filesystem path to the repository root used for investigation.
        Must exist and be a directory; ValueError is raised otherwise.
    test_path:
        Filesystem path passed to run_validation as the test target.
        When None (default), ``repository_path`` is used as the test target,
        matching the same convention as POST /api/validate when both env-var
        overrides point to the same directory.

    Returns
    -------
    EngineeringReport
        Fully-populated report combining investigation and validation results.

    Raises
    ------
    ValueError
        When ``issue`` is empty or ``repository_path`` is invalid — propagated
        directly from investigate_issue without modification.

    Notes
    -----
    run_validation never raises for normal pytest outcomes; infrastructure
    problems are reflected in the returned ValidateResponse as status="error".
    """
    # ------------------------------------------------------------------
    # Step 1 — investigate
    # May raise ValueError for invalid inputs; caller handles this.
    # ------------------------------------------------------------------
    investigation = investigate_issue(issue=issue, repository_path=repository_path)

    # ------------------------------------------------------------------
    # Step 2 — validate
    # Use test_path when provided; fall back to repository_path.
    # run_validation never raises — returns status="error" on problems.
    # ------------------------------------------------------------------
    resolved_test_path = test_path if test_path is not None else repository_path
    validation = run_validation(resolved_test_path)

    # ------------------------------------------------------------------
    # Step 3 — compose report
    # build_engineering_report is a pure function; no side effects.
    # ------------------------------------------------------------------
    return build_engineering_report(investigation=investigation, validation=validation)
