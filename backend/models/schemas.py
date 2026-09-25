"""
Shared Pydantic API schemas for RepoMedic.

Approved contract (massiplanvF, confirmed Increment 2):
  - InvestigateResponse.test_generated : str
      The regression-test recommendation text.
  - InvestigateResponse.confidence     : float  (0.0 – 1.0)
      Numeric confidence score for the investigation result.

Note: HACKATHON_EXECUTION_PLAN.md section 22 shows different types for
these two fields (bool / str).  That document will be synchronised
separately.  The massiplanvF contract is authoritative for this
increment.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Investigation
# ---------------------------------------------------------------------------


class InvestigateRequest(BaseModel):
    """Request body for POST /api/investigate."""

    issue: str = Field(..., min_length=1, description="Description of the bug or issue to investigate.")


class InvestigateResponse(BaseModel):
    """Response body for POST /api/investigate."""

    issue: str = Field(..., description="The original issue description echoed back.")
    relevant_files: List[str] = Field(
        ..., description="Repository files most relevant to the issue."
    )
    root_cause: str = Field(..., description="Likely root cause of the issue.")
    suggested_fix: str = Field(..., description="Recommended repair for the root cause.")
    test_generated: str = Field(
        ..., description="Regression-test recommendation text."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the investigation result (0.0 – 1.0).",
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class ValidateResponse(BaseModel):
    """Response body for POST /api/validate."""

    tests_run: int = Field(..., ge=0, description="Total number of tests executed.")
    passed: int = Field(..., ge=0, description="Number of tests that passed.")
    failed: int = Field(..., ge=0, description="Number of tests that failed.")
    status: Literal["passed", "failed", "error"] = Field(
        ..., description="Overall validation outcome."
    )
