"""Single execution-policy boundary for repository-scoped operations."""
from backend.analyzers.engine import analyze_repository
from backend.models.repositories import EngineeringReportV1, ValidationResult
from backend.services.investigation import investigate_issue
from backend.services.validation import run_validation
from backend.services.workflow import run_engineering_workflow


def analyze(workspace):
    result = analyze_repository(workspace.root)
    result["repository"] = workspace.display_name
    return result


def investigate(workspace, issue):
    return investigate_issue(issue, str(workspace.root))


def blocked_validation():
    return ValidationResult(status="not_run", reason="untrusted_repository")


def validate(workspace):
    if not workspace.trusted_demo:
        return blocked_validation()
    return ValidationResult(**run_validation(str(workspace.root)).model_dump())


def workflow(workspace, issue):
    result = run_engineering_workflow(
        issue, str(workspace.root),
        validation_override=None if workspace.trusted_demo else blocked_validation(),
    )
    return EngineeringReportV1(**result.model_dump())
