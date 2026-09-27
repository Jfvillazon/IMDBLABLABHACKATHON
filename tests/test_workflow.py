"""
Integration tests for backend/services/workflow.py

Covers the full pipeline:
    issue → investigation → validation → EngineeringReport

All investigation tests use temporary directories so there is no
dependency on sample_repo/ contents or teammate work.

Required coverage (as specified in TASK 09):
  - investigation result flows correctly into EngineeringReport
  - validation result flows correctly into EngineeringReport
  - issue is preserved
  - relevant_files are preserved
  - root_cause is preserved
  - suggested_fix is preserved
  - regression_test maps correctly from test_generated
  - confidence is preserved
  - validation counts/status are preserved
  - passed validation produces the correct outcome semantics
  - failed validation produces the correct outcome semantics
  - validation error produces the correct outcome semantics
  - invalid investigation inputs fail safely
  - the analyzed repository is not modified
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models.schemas import EngineeringReport, InvestigateResponse, ValidateResponse
from backend.services.report import _OUTCOME_ERROR, _OUTCOME_FAILED, _OUTCOME_PASSED
from backend.services.workflow import run_engineering_workflow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(*files: tuple[str, str]) -> tempfile.TemporaryDirectory:
    """
    Create a temporary directory tree with the given (rel_path, content) pairs.
    Returns the TemporaryDirectory; caller is responsible for cleanup.
    """
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for rel, content in files:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp


def _stub_validation_passed() -> ValidateResponse:
    return ValidateResponse(tests_run=5, passed=5, failed=0, status="passed")


def _stub_validation_failed() -> ValidateResponse:
    return ValidateResponse(tests_run=5, passed=3, failed=2, status="failed")


def _stub_validation_error() -> ValidateResponse:
    return ValidateResponse(tests_run=0, passed=0, failed=0, status="error")


# ---------------------------------------------------------------------------
# Field-preservation tests — investigate result flows into report
# ---------------------------------------------------------------------------


class TestInvestigationFlowsIntoReport:
    """Verify every InvestigateResponse field is accurately reflected in the report."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("checkout.py", "def checkout(quantity):\n    return quantity * 10\n"),
        )

    def teardown_method(self):
        self.tmp.cleanup()

    def _run(self, issue: str, validation: ValidateResponse) -> EngineeringReport:
        with patch(
            "backend.services.workflow.run_validation", return_value=validation
        ):
            return run_engineering_workflow(
                issue=issue,
                repository_path=self.tmp.name,
            )

    def test_issue_preserved(self):
        issue = "Checkout crashes when quantity is missing."
        report = self._run(issue, _stub_validation_passed())
        assert report.issue == issue

    def test_relevant_files_preserved(self):
        # The investigation engine should rank checkout.py relevant for a checkout issue.
        report = self._run(
            "Checkout crashes when quantity is missing.", _stub_validation_passed()
        )
        # relevant_files may be empty if nothing scored, but must be a list.
        assert isinstance(report.relevant_files, list)

    def test_relevant_files_match_investigation(self):
        """Workflow report relevant_files must equal what investigate_issue returned."""
        issue = "Checkout crashes when quantity is missing."
        # Run investigation separately to get the ground truth.
        from backend.services.investigation import investigate_issue

        investigation = investigate_issue(
            issue=issue, repository_path=self.tmp.name
        )
        report = self._run(issue, _stub_validation_passed())
        assert report.relevant_files == investigation.relevant_files

    def test_root_cause_preserved(self):
        issue = "Checkout crashes when quantity is missing."
        from backend.services.investigation import investigate_issue

        investigation = investigate_issue(issue=issue, repository_path=self.tmp.name)
        report = self._run(issue, _stub_validation_passed())
        assert report.root_cause == investigation.root_cause

    def test_suggested_fix_preserved(self):
        issue = "Checkout crashes when quantity is missing."
        from backend.services.investigation import investigate_issue

        investigation = investigate_issue(issue=issue, repository_path=self.tmp.name)
        report = self._run(issue, _stub_validation_passed())
        assert report.suggested_fix == investigation.suggested_fix

    def test_regression_test_maps_from_test_generated(self):
        """EngineeringReport.regression_test must equal InvestigateResponse.test_generated."""
        issue = "Checkout crashes when quantity is missing."
        from backend.services.investigation import investigate_issue

        investigation = investigate_issue(issue=issue, repository_path=self.tmp.name)
        report = self._run(issue, _stub_validation_passed())
        assert report.regression_test == investigation.test_generated

    def test_confidence_preserved(self):
        issue = "Checkout crashes when quantity is missing."
        from backend.services.investigation import investigate_issue

        investigation = investigate_issue(issue=issue, repository_path=self.tmp.name)
        report = self._run(issue, _stub_validation_passed())
        assert report.confidence == pytest.approx(investigation.confidence)


# ---------------------------------------------------------------------------
# Field-preservation tests — validation result flows into report
# ---------------------------------------------------------------------------


class TestValidationFlowsIntoReport:
    """Verify every ValidateResponse field is accurately reflected in the report."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("app.py", "# placeholder\n"),
        )

    def teardown_method(self):
        self.tmp.cleanup()

    def _run(self, validation: ValidateResponse) -> EngineeringReport:
        with patch(
            "backend.services.workflow.run_validation", return_value=validation
        ):
            return run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
            )

    def test_tests_run_preserved_passed(self):
        v = _stub_validation_passed()
        report = self._run(v)
        assert report.tests_run == v.tests_run

    def test_passed_count_preserved(self):
        v = _stub_validation_passed()
        report = self._run(v)
        assert report.passed == v.passed

    def test_failed_count_preserved_from_failed(self):
        v = _stub_validation_failed()
        report = self._run(v)
        assert report.failed == v.failed

    def test_validation_status_passed_preserved(self):
        v = _stub_validation_passed()
        report = self._run(v)
        assert report.validation_status == "passed"

    def test_validation_status_failed_preserved(self):
        v = _stub_validation_failed()
        report = self._run(v)
        assert report.validation_status == "failed"

    def test_validation_status_error_preserved(self):
        v = _stub_validation_error()
        report = self._run(v)
        assert report.validation_status == "error"

    def test_tests_run_preserved_error(self):
        v = _stub_validation_error()
        report = self._run(v)
        assert report.tests_run == 0
        assert report.passed == 0
        assert report.failed == 0


# ---------------------------------------------------------------------------
# Outcome-semantics tests
# ---------------------------------------------------------------------------


class TestOutcomeSemantics:
    """Verify outcome text is semantically correct for each validation status."""

    def setup_method(self):
        self.tmp = _make_repo(("app.py", "# placeholder\n"))

    def teardown_method(self):
        self.tmp.cleanup()

    def _run(self, validation: ValidateResponse) -> EngineeringReport:
        with patch(
            "backend.services.workflow.run_validation", return_value=validation
        ):
            return run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
            )

    def test_passed_outcome_contains_passed(self):
        report = self._run(_stub_validation_passed())
        assert "passed" in report.outcome.lower()

    def test_passed_outcome_does_not_claim_repair_applied(self):
        report = self._run(_stub_validation_passed())
        outcome = report.outcome.lower()
        assert "repair has been applied" not in outcome
        assert "fix has been applied" not in outcome
        assert "bug is fixed" not in outcome
        assert "bug has been fixed" not in outcome

    def test_passed_outcome_does_not_falsely_claim_test_file_created(self):
        report = self._run(_stub_validation_passed())
        outcome = report.outcome.lower()
        # Acceptable: negated language; not acceptable: affirmative claims
        assert "we created a regression test" not in outcome
        assert "regression test was created" not in outcome

    def test_failed_outcome_contains_failed(self):
        report = self._run(_stub_validation_failed())
        assert "failed" in report.outcome.lower()

    def test_failed_outcome_mentions_further_action_needed(self):
        report = self._run(_stub_validation_failed())
        outcome = report.outcome.lower()
        assert any(
            phrase in outcome
            for phrase in ("required", "repair", "further", "investigation")
        )

    def test_error_outcome_contains_error(self):
        report = self._run(_stub_validation_error())
        assert "error" in report.outcome.lower()

    def test_error_outcome_no_false_conclusion(self):
        report = self._run(_stub_validation_error())
        outcome = report.outcome.lower()
        assert "all tests passed" not in outcome
        assert "tests failed" not in outcome

    def test_outcome_is_non_empty_string(self):
        for v in (_stub_validation_passed(), _stub_validation_failed(), _stub_validation_error()):
            report = self._run(v)
            assert isinstance(report.outcome, str)
            assert len(report.outcome) > 0

    def test_three_outcomes_are_distinct(self):
        r_passed = self._run(_stub_validation_passed())
        r_failed = self._run(_stub_validation_failed())
        r_error = self._run(_stub_validation_error())
        assert r_passed.outcome != r_failed.outcome
        assert r_passed.outcome != r_error.outcome
        assert r_failed.outcome != r_error.outcome


# ---------------------------------------------------------------------------
# Invalid-input safety tests
# ---------------------------------------------------------------------------


class TestInvalidInputSafety:
    """Verify the workflow fails safely on invalid investigation inputs."""

    def setup_method(self):
        self.tmp = _make_repo(("app.py", "# placeholder\n"))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_empty_issue_raises_value_error(self):
        with pytest.raises(ValueError, match="[Ii]ssue"):
            run_engineering_workflow(issue="", repository_path=self.tmp.name)

    def test_whitespace_only_issue_raises_value_error(self):
        with pytest.raises(ValueError, match="[Ii]ssue"):
            run_engineering_workflow(issue="   ", repository_path=self.tmp.name)

    def test_nonexistent_repository_raises_value_error(self):
        with pytest.raises(ValueError):
            run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path="/tmp/__repo_medic_nonexistent_path_xyz__",
            )

    def test_file_as_repository_raises_value_error(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp_file.close()
        try:
            with pytest.raises(ValueError):
                run_engineering_workflow(
                    issue="Checkout crashes when quantity is missing.",
                    repository_path=tmp_file.name,
                )
        finally:
            os.unlink(tmp_file.name)

    def test_empty_issue_does_not_invoke_validation(self):
        """run_validation must NOT be called when investigation raises."""
        with patch(
            "backend.services.workflow.run_validation"
        ) as mock_validate:
            with pytest.raises(ValueError):
                run_engineering_workflow(issue="", repository_path=self.tmp.name)
            mock_validate.assert_not_called()


# ---------------------------------------------------------------------------
# Repository immutability tests
# ---------------------------------------------------------------------------


class TestRepositoryNotModified:
    """Verify the workflow never modifies the analyzed repository."""

    def test_no_files_created_in_repository(self):
        tmp = _make_repo(
            ("checkout.py", "def checkout(quantity):\n    return quantity * 10\n"),
            ("cart.py", "items = []\n"),
        )
        try:
            root = Path(tmp.name)
            before = set(root.rglob("*"))

            with patch(
                "backend.services.workflow.run_validation",
                return_value=_stub_validation_passed(),
            ):
                run_engineering_workflow(
                    issue="Checkout crashes when quantity is missing.",
                    repository_path=tmp.name,
                )

            after = set(root.rglob("*"))
            assert before == after, (
                f"Repository was modified. New/removed paths: {before.symmetric_difference(after)}"
            )
        finally:
            tmp.cleanup()

    def test_no_files_modified_in_repository(self):
        tmp = _make_repo(
            ("checkout.py", "def checkout(quantity):\n    return quantity * 10\n"),
        )
        try:
            root = Path(tmp.name)
            checkout = root / "checkout.py"
            original_content = checkout.read_text(encoding="utf-8")
            original_mtime = checkout.stat().st_mtime

            with patch(
                "backend.services.workflow.run_validation",
                return_value=_stub_validation_passed(),
            ):
                run_engineering_workflow(
                    issue="Checkout crashes when quantity is missing.",
                    repository_path=tmp.name,
                )

            assert checkout.read_text(encoding="utf-8") == original_content
            assert checkout.stat().st_mtime == original_mtime
        finally:
            tmp.cleanup()


# ---------------------------------------------------------------------------
# Return type and structure tests
# ---------------------------------------------------------------------------


class TestReturnType:
    """Verify the workflow always returns a valid EngineeringReport."""

    def setup_method(self):
        self.tmp = _make_repo(("app.py", "# placeholder\n"))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_returns_engineering_report_instance(self):
        with patch(
            "backend.services.workflow.run_validation",
            return_value=_stub_validation_passed(),
        ):
            result = run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
            )
        assert isinstance(result, EngineeringReport)

    def test_serializes_to_dict_with_expected_keys(self):
        with patch(
            "backend.services.workflow.run_validation",
            return_value=_stub_validation_passed(),
        ):
            result = run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
            )
        data = result.model_dump()
        expected_keys = {
            "issue",
            "relevant_files",
            "root_cause",
            "suggested_fix",
            "regression_test",
            "confidence",
            "tests_run",
            "passed",
            "failed",
            "validation_status",
            "outcome",
        }
        assert set(data.keys()) == expected_keys

    def test_confidence_in_range(self):
        with patch(
            "backend.services.workflow.run_validation",
            return_value=_stub_validation_passed(),
        ):
            result = run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
            )
        assert 0.0 <= result.confidence <= 1.0


# ---------------------------------------------------------------------------
# test_path parameter tests
# ---------------------------------------------------------------------------


class TestTestPathParameter:
    """Verify the optional test_path parameter is forwarded correctly."""

    def setup_method(self):
        self.tmp = _make_repo(("app.py", "# placeholder\n"))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_explicit_test_path_forwarded_to_validation(self):
        explicit_path = "/tmp/__test_path_sentinel__"
        with patch(
            "backend.services.workflow.run_validation",
            return_value=_stub_validation_passed(),
        ) as mock_validate:
            run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
                test_path=explicit_path,
            )
        mock_validate.assert_called_once_with(explicit_path)

    def test_none_test_path_uses_repository_path(self):
        with patch(
            "backend.services.workflow.run_validation",
            return_value=_stub_validation_passed(),
        ) as mock_validate:
            run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
                test_path=None,
            )
        mock_validate.assert_called_once_with(self.tmp.name)

    def test_default_test_path_uses_repository_path(self):
        """Calling without test_path kwarg should default to repository_path."""
        with patch(
            "backend.services.workflow.run_validation",
            return_value=_stub_validation_passed(),
        ) as mock_validate:
            run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
            )
        mock_validate.assert_called_once_with(self.tmp.name)


# ---------------------------------------------------------------------------
# Execution-sequence tests
# ---------------------------------------------------------------------------


class TestExecutionSequence:
    """Verify investigation → validation → report order is respected."""

    def setup_method(self):
        self.tmp = _make_repo(("app.py", "# placeholder\n"))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_investigate_called_before_validate(self):
        call_order = []

        def fake_investigate(issue, repository_path):
            call_order.append("investigate")
            return InvestigateResponse(
                issue=issue,
                relevant_files=[],
                root_cause="cause",
                suggested_fix="fix",
                test_generated="test rec",
                confidence=0.9,
            )

        def fake_validate(test_path):
            call_order.append("validate")
            return _stub_validation_passed()

        with (
            patch("backend.services.workflow.investigate_issue", side_effect=fake_investigate),
            patch("backend.services.workflow.run_validation", side_effect=fake_validate),
        ):
            run_engineering_workflow(
                issue="Checkout crashes when quantity is missing.",
                repository_path=self.tmp.name,
            )

        assert call_order == ["investigate", "validate"]

    def test_validate_not_called_when_investigate_raises(self):
        def raise_value_error(issue, repository_path):
            raise ValueError("bad input")

        with (
            patch("backend.services.workflow.investigate_issue", side_effect=raise_value_error),
            patch("backend.services.workflow.run_validation") as mock_validate,
        ):
            with pytest.raises(ValueError):
                run_engineering_workflow(
                    issue="some issue",
                    repository_path=self.tmp.name,
                )
        mock_validate.assert_not_called()
