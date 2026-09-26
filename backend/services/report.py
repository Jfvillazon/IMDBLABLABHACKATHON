"""
Report Service — RepoMedic.

Public interface:
    build_engineering_report(
        investigation: InvestigateResponse,
        validation: ValidateResponse,
    ) -> EngineeringReport

Composes an already-computed InvestigateResponse and ValidateResponse into a
single deterministic EngineeringReport.  This function:

  - does NOT rerun investigation
  - does NOT rerun pytest
  - does NOT call any external service
  - does NOT write to the filesystem
  - does NOT modify any repository
  - does NOT mutate its inputs
"""

from __future__ import annotations

from backend.models.schemas import EngineeringReport, InvestigateResponse, ValidateResponse

# ---------------------------------------------------------------------------
# Outcome messages
# ---------------------------------------------------------------------------

_OUTCOME_PASSED = (
    "Validation completed successfully: all {tests_run} executed test(s) passed. "
    "Note: passing tests indicate that the regression-test suite ran without "
    "failures; they do not confirm that a repair has been physically applied to "
    "the repository or that a regression test file has been created."
)

_OUTCOME_FAILED = (
    "Validation completed but {failed} of {tests_run} executed test(s) failed. "
    "The suggested repair and regression-test recommendation have not been applied "
    "automatically. Further investigation or manual repair is required before "
    "validation can pass."
)

_OUTCOME_ERROR = (
    "Validation could not be completed reliably (status: error). "
    "The validation environment or result should be checked. "
    "No conclusion about test passage or repair effectiveness can be drawn."
)


# ---------------------------------------------------------------------------
# Outcome builder
# ---------------------------------------------------------------------------


def _build_outcome(status: str, tests_run: int, failed: int) -> str:
    """
    Return a concise, technically accurate outcome string based on
    *status*.  Never claims repairs were applied or test files created.
    """
    if status == "passed":
        return _OUTCOME_PASSED.format(tests_run=tests_run)
    if status == "failed":
        return _OUTCOME_FAILED.format(failed=failed, tests_run=tests_run)
    # "error" (and any unexpected value treated conservatively)
    return _OUTCOME_ERROR


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def build_engineering_report(
    investigation: InvestigateResponse,
    validation: ValidateResponse,
) -> EngineeringReport:
    """
    Compose *investigation* and *validation* into an EngineeringReport.

    Parameters
    ----------
    investigation:
        Already-computed InvestigateResponse.  Not mutated.
    validation:
        Already-computed ValidateResponse.  Not mutated.

    Returns
    -------
    EngineeringReport
        Deterministic report; output depends only on the two inputs.
    """
    outcome = _build_outcome(
        status=validation.status,
        tests_run=validation.tests_run,
        failed=validation.failed,
    )

    return EngineeringReport(
        issue=investigation.issue,
        relevant_files=list(investigation.relevant_files),
        root_cause=investigation.root_cause,
        suggested_fix=investigation.suggested_fix,
        regression_test=investigation.test_generated,
        confidence=investigation.confidence,
        tests_run=validation.tests_run,
        passed=validation.passed,
        failed=validation.failed,
        validation_status=validation.status,
        outcome=outcome,
    )
