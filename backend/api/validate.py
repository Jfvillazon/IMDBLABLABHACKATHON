"""
POST /api/validate — HTTP layer for the Validation Engine.

The public API contract remains unchanged:
    POST /api/validate
    No request body.

For the interactive RepoMedic application, validation can run against the
repository currently selected through the repository-selection workflow.

The original path resolver remains available for backward compatibility
with the existing project structure and tests.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter

from backend.models.schemas import ValidateResponse
from backend.services.repository_session import get_active_repository
from backend.services.validation import run_validation


router = APIRouter()


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_TEST_PATH = _PROJECT_ROOT / "sample_repo"


def _resolve_test_path() -> str:
    """Return the original configured validation path."""
    override = os.environ.get("REPO_MEDIC_TEST_PATH", "").strip()

    if override:
        return override

    repo_override = os.environ.get("REPO_MEDIC_REPO_PATH", "").strip()

    if repo_override:
        return repo_override

    return str(_DEFAULT_TEST_PATH)


@router.post("/api/validate", response_model=ValidateResponse)
def validate() -> ValidateResponse:
    """
    Run the controlled test suite.

    Explicit configuration keeps priority. Otherwise, RepoMedic uses the
    repository selected through the interactive repository workflow.
    """
    resolved_path = _resolve_test_path()

    default_path = str(_DEFAULT_TEST_PATH)

    if resolved_path != default_path:
        test_path = resolved_path
    else:
        test_path = str(get_active_repository())

    return run_validation(test_path)