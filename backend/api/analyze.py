from fastapi import APIRouter
from pathlib import Path

from backend.analyzers.repository import scan_repository
from backend.analyzers.quality import analyze_quality
from backend.analyzers.testing import analyze_testing
from backend.analyzers.security import analyze_security


router = APIRouter()


@router.post("/api/analyze")
def analyze_repository():

    repo_path = Path("sample_repo")

    repository = scan_repository(str(repo_path))

    files = repository["files"]

    findings = []

    findings.extend(
        analyze_quality(files, repo_path)
    )

    findings.extend(
        analyze_testing(files, repo_path)
    )

    findings.extend(
        analyze_security(files, repo_path)
    )

    # documentation analyzer here

    for index, finding in enumerate(findings, start=1):
        finding["id"] = f"F{index:03}"

    health_score = calculate_health_score(findings)

    return {
        "repository": repository["repository"],
        "files_analyzed": repository["files_analyzed"],
        "languages": repository["languages"],
        "health_score": health_score,
        "findings": findings
    }