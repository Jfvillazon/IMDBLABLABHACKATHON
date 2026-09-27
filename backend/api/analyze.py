"""Read-only FastAPI endpoint using a server-controlled repository root.

Do not accept client-supplied local paths or Git URLs. Those require separate
sandboxing, authorization, download limits, and SSRF prevention.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.analyzers.engine import analyze_repository

LOGGER = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class FindingResponse(BaseModel):
    id: str
    category: str
    severity: Literal["high", "medium", "low"]
    title: str
    file: str
    line: int | None
    description: str
    recommendation: str


class AnalyzeResponse(BaseModel):
    repository: str
    files_analyzed: int = Field(ge=0)
    languages: list[str]
    health_score: int = Field(ge=0, le=100)
    findings: list[FindingResponse]


def configured_repository_root() -> Path:
    """Resolve the *server-selected* repository independently of the process CWD.

    A relative REPOMEDIC_SAMPLE_REPO is relative to the project root, not to
    whichever folder the developer happened to launch Uvicorn from. No HTTP
    request data is ever used to choose a filesystem path.
    """
    configured = os.environ.get("REPOMEDIC_SAMPLE_REPO")
    if not configured:
        return PROJECT_ROOT / "sample_repo"
    root = Path(configured).expanduser()
    return root if root.is_absolute() else PROJECT_ROOT / root


@router.post("/api/analyze", response_model=AnalyzeResponse)
def analyze() -> AnalyzeResponse:
    # Configured by the server operator, NEVER supplied in the HTTP request.
    root = configured_repository_root()
    try:
        return AnalyzeResponse(**analyze_repository(root))
    except (ValueError, OSError):
        LOGGER.warning("Repository analysis unavailable; verify the configured sample repository")
        raise HTTPException(status_code=503, detail="Repository analysis is temporarily unavailable") from None
