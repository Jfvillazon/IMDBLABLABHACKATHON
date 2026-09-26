"""
POST /api/investigate — HTTP layer for the Investigation Engine.

Design decisions:
  - repository_path is NOT a user-supplied parameter.
    The approved API contract (HACKATHON_EXECUTION_PLAN.md §22 and
    massiplanvF Phase 6) only shows {"issue": ...} in the request body.
    The InvestigateRequest schema also contains only `issue`.
    The endpoint therefore resolves the repository path internally,
    defaulting to the project-relative `sample_repo/` directory.
    This can be overridden at startup via the REPO_MEDIC_REPO_PATH
    environment variable without changing the public API contract.

  - Business logic stays in backend/services/investigation.py.
    This module is intentionally thin: validate → call service → return.

  - ValueError from the service maps to HTTP 422 (Unprocessable Entity)
    so callers receive a meaningful JSON error rather than a 500.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.models.schemas import InvestigateRequest, InvestigateResponse
from backend.services.investigation import investigate_issue

router = APIRouter()

# ---------------------------------------------------------------------------
# Repository path resolution
# ---------------------------------------------------------------------------
# Default: <project_root>/sample_repo
# Override: set REPO_MEDIC_REPO_PATH environment variable.
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_REPO_PATH = _PROJECT_ROOT / "sample_repo"


def _resolve_repo_path() -> str:
    """Return the repository path to investigate against."""
    override = os.environ.get("REPO_MEDIC_REPO_PATH", "").strip()
    if override:
        return override
    return str(_DEFAULT_REPO_PATH)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/api/investigate", response_model=InvestigateResponse)
def investigate(request: InvestigateRequest) -> InvestigateResponse:
    """
    Investigate a reported issue against the configured repository.

    - Accepts an InvestigateRequest with a non-empty `issue` string.
    - Delegates to the Investigation Engine (investigate_issue).
    - Returns a fully-populated InvestigateResponse.
    - Maps ValueError (invalid input, missing path) → HTTP 422.
    """
    repository_path = _resolve_repo_path()

    try:
        result = investigate_issue(
            issue=request.issue,
            repository_path=repository_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return result
