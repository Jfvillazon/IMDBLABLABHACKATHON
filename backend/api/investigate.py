"""
POST /api/investigate — HTTP layer for the Investigation Engine.

The public request contract remains:
    {"issue": "..."}

For the interactive RepoMedic application, investigation can use the
repository currently selected through the repository-selection workflow.

The original repository resolver remains available for backward
compatibility with the existing project structure and tests.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.models.schemas import InvestigateRequest, InvestigateResponse
from backend.services.investigation import investigate_issue
from backend.services.repository_session import get_active_repository


router = APIRouter()


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_REPO_PATH = _PROJECT_ROOT / "sample_repo"


def _resolve_repo_path() -> str:
    """Return the original configured repository path."""
    override = os.environ.get("REPO_MEDIC_REPO_PATH", "").strip()

    if override:
        return override

    return str(_DEFAULT_REPO_PATH)


@router.post("/api/investigate", response_model=InvestigateResponse)
def investigate(request: InvestigateRequest) -> InvestigateResponse:
    """
    Investigate a reported issue.

    Explicit configuration keeps priority. Otherwise, RepoMedic uses the
    repository selected through the interactive repository workflow.
    """
    resolved_path = _resolve_repo_path()

    default_path = str(_DEFAULT_REPO_PATH)

    if resolved_path != default_path:
        repository_path = resolved_path
    else:
        repository_path = str(get_active_repository())

    try:
        result = investigate_issue(
            issue=request.issue,
            repository_path=repository_path,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return result