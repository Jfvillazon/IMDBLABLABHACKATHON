"""
POST /api/validate — HTTP layer for the Validation Engine.

Design decisions:
  - No request body is required.
    The approved contract (massiplanvF Phase 9, schemas.py ValidateResponse)
    defines no user-supplied parameters for validation — the test target
    is resolved server-side, matching the same pattern as /api/investigate.
    This prevents arbitrary filesystem execution through the public API.

  - The test path defaults to the project-relative `sample_repo/` directory.
    Override at startup via REPO_MEDIC_TEST_PATH environment variable.
    If REPO_MEDIC_REPO_PATH is set, it is used as the fallback so both
    endpoints can share the same override in simple deployments.

  - Business logic stays in backend/services/validation.py.
    This module is intentionally thin: resolve path → call service → return.

  - The service always returns a ValidateResponse (never raises for normal
    pytest outcomes), so this endpoint maps no service errors to 500.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter

from backend.models.schemas import ValidateResponse
from backend.services.validation import run_validation

router = APIRouter()

# ---------------------------------------------------------------------------
# Test path resolution
# ---------------------------------------------------------------------------
# Priority:
#   1. REPO_MEDIC_TEST_PATH  — explicit override for the test target
#   2. REPO_MEDIC_REPO_PATH  — shared repo-path override (investigate compat)
#   3. <project_root>/sample_repo  — default
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_TEST_PATH = _PROJECT_ROOT / "sample_repo"


def _resolve_test_path() -> str:
    """Return the test path to run validation against."""
    override = os.environ.get("REPO_MEDIC_TEST_PATH", "").strip()
    if override:
        return override
    repo_override = os.environ.get("REPO_MEDIC_REPO_PATH", "").strip()
    if repo_override:
        return repo_override
    return str(_DEFAULT_TEST_PATH)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/api/validate", response_model=ValidateResponse)
def validate() -> ValidateResponse:
    """
    Run the controlled test suite against the configured test path.

    - No request body — the test target is resolved server-side.
    - Delegates to the Validation Engine (run_validation).
    - Returns a fully-populated ValidateResponse.
    - Validation failures (pytest exits non-zero) are results, not errors.
    - Infrastructure problems (missing path, timeout) return status="error".
    """
    test_path = _resolve_test_path()
    return run_validation(test_path)
