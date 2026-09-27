"""Additive repository-scoped contracts; legacy schemas remain unchanged."""
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.api.analyze import AnalyzeResponse
from backend.models.schemas import EngineeringReport, InvestigateResponse


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GithubRequest(StrictRequest):
    url: str = Field(min_length=1, max_length=512)


class RepositoryIssue(StrictRequest):
    issue: str = Field(min_length=1, max_length=10000)


class Capabilities(BaseModel):
    analyze: bool = True
    investigate: bool = True
    can_validate: bool = Field(default=False, alias="validate")


class RepositoryDescriptor(BaseModel):
    repository_id: str
    source: Literal["demo", "github", "zip"]
    display_name: str
    status: Literal["ready"] = "ready"
    created_at: datetime
    expires_at: datetime
    capabilities: Capabilities
    source_details: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ScopedAnalysis(BaseModel):
    repository_id: str
    analysis: AnalyzeResponse


class ScopedInvestigation(BaseModel):
    repository_id: str
    investigation: InvestigateResponse


class ValidationResult(BaseModel):
    tests_run: int = Field(default=0, ge=0)
    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    status: Literal["passed", "failed", "error", "not_run"]
    reason: Optional[Literal["untrusted_repository"]] = None


class ScopedValidation(BaseModel):
    repository_id: str
    validation: ValidationResult


class EngineeringReportV1(EngineeringReport):
    validation_status: Literal["passed", "failed", "error", "not_run"]
    validation_reason: Optional[Literal["untrusted_repository"]] = None


class ScopedWorkflow(BaseModel):
    repository_id: str
    report: EngineeringReportV1
