"""Shared contract for Member 1's /api/investigate endpoint.

The response reflects the final approved frontend/backend contract:
- test_generated is a regression-test *recommendation*, not a boolean.
- confidence is a numeric score between 0.0 and 1.0.

This model does NOT implement or register /api/investigate; that endpoint and
its investigation service belong to Member 1. Do not create a competing route.
"""
from pydantic import BaseModel, ConfigDict, Field


class InvestigationResponse(BaseModel):
    """Approved JSON response for POST /api/investigate."""

    model_config = ConfigDict(extra="forbid")

    issue: str = Field(min_length=1)
    relevant_files: list[str]
    root_cause: str = Field(min_length=1)
    suggested_fix: str = Field(min_length=1)
    test_generated: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
