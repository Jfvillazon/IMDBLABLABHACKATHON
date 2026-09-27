"""
Shared Pydantic API schemas for RepoMedic.

Approved contract (massiplanvF, confirmed Increment 2):
  - InvestigateResponse.test_generated : str
      The regression-test recommendation text.
  - InvestigateResponse.confidence     : float  (0.0 – 1.0)
      Numeric confidence score for the investigation result.

Member 2 contract (dev-2, InvestigationResponse):
  - Extra fields are forbidden.
  - confidence rejects NaN and ±Inf.
  - test_generated must be a non-empty string.
"""

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Investigation (Member 2 — strict schema for test_investigation_schema.py)
# ---------------------------------------------------------------------------


class InvestigationResponse(BaseModel):
    """Approved JSON response for POST /api/investigate — strict Member 2 contract."""

    model_config = ConfigDict(extra="forbid")

    issue: str = Field(min_length=1)
    relevant_files: list[str]
    root_cause: str = Field(min_length=1)
    suggested_fix: str = Field(min_length=1)
    test_generated: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)


# ---------------------------------------------------------------------------
# Investigation (Member 1 — used by investigate API and services)
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


# ---------------------------------------------------------------------------
# Engineering Report
# ---------------------------------------------------------------------------


class EngineeringReport(BaseModel):
    """Combined engineering report produced by build_engineering_report."""

    issue: str = Field(..., description="The original issue description.")
    relevant_files: List[str] = Field(
        ..., description="Repository files most relevant to the issue."
    )
    root_cause: str = Field(..., description="Likely root cause of the issue.")
    suggested_fix: str = Field(..., description="Recommended repair for the root cause.")
    regression_test: str = Field(
        ..., description="Regression-test recommendation text."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the investigation result (0.0 – 1.0).",
    )
    tests_run: int = Field(..., ge=0, description="Total number of tests executed.")
    passed: int = Field(..., ge=0, description="Number of tests that passed.")
    failed: int = Field(..., ge=0, description="Number of tests that failed.")
    validation_status: Literal["passed", "failed", "error"] = Field(
        ..., description="Overall validation outcome."
    )
    outcome: str = Field(
        ..., description="Concise engineering outcome derived from the validation result."
    )
