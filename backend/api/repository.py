"""Repository-selection API for the RepoMedic interactive application.

This endpoint is separate from the original /api/analyze contract so the
existing demo API remains backward compatible.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.analyzers.engine import analyze_repository
from backend.services.github_repository import (
    GitHubRepositoryError,
    clone_github_repository,
)
from backend.services.repository_session import set_active_repository


router = APIRouter(tags=["repository"])


class RepositoryAnalyzeRequest(BaseModel):
    source_type: Literal["local", "github"]
    repository: str = Field(min_length=1)


class FindingResponse(BaseModel):
    id: str
    category: str
    severity: Literal["high", "medium", "low"]
    title: str
    file: str
    line: int | None
    description: str
    recommendation: str


class RepositoryAnalyzeResponse(BaseModel):
    repository: str
    files_analyzed: int
    languages: list[str]
    health_score: int
    findings: list[FindingResponse]


@router.post(
    "/api/repository/analyze",
    response_model=RepositoryAnalyzeResponse,
)
def analyze_selected_repository(
    request: RepositoryAnalyzeRequest,
) -> RepositoryAnalyzeResponse:
    """Select and analyze a local or public GitHub repository."""

    repository = request.repository.strip()

    if not repository:
        raise HTTPException(
            status_code=422,
            detail="Repository is required.",
        )

    try:
        if request.source_type == "github":
            root = clone_github_repository(repository)
        else:
            root = repository

        active_root = set_active_repository(root)

        result = analyze_repository(active_root)

        return RepositoryAnalyzeResponse(**result)

    except GitHubRepositoryError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except OSError:
        raise HTTPException(
            status_code=503,
            detail="Repository analysis is temporarily unavailable.",
        ) from None