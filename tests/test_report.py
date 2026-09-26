"""
Tests for backend/services/report.py

Covers:
  - report correctly copies issue
  - relevant files preserved
  - root cause preserved
  - suggested repair preserved
  - test_generated maps correctly to regression_test
  - confidence preserved
  - validation counts preserved
  - passed validation produces accurate successful outcome
  - failed validation produces accurate failure outcome
  - error validation produces accurate error outcome
  - report does not claim repair was applied
  - report does not claim regression test was physically created
  - inputs are not mutated
  - deterministic output (same inputs → same output)
  - EngineeringReport serializes correctly
  - existing InvestigateResponse unchanged
  - existing ValidateResponse unchanged
"""

import pytest
from pydantic import ValidationError

from backend.models.schemas import EngineeringReport, InvestigateResponse, ValidateResponse
from backend.services.report import build_engineering_report


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_INVESTIGATION = InvestigateResponse(
    issue="Checkout crashes on missing quantity.",
    relevant_files=["checkout.py", "cart.py"],
    root_cause="The quantity input is used before being validated.",
    suggested_fix="Validate the quantity field before performing checkout calculations.",
    test_generated="Add a regression test that calls checkout with quantity=None.",
    confidence=0.90,
)

SAMPLE_VALIDATION_PASSED = ValidateResponse(
    tests_run=10,
    passed=10,
    failed=0,
    status="passed",
)

SAMPLE_VALIDATION_FAILED = ValidateResponse(
    tests_run=10,
    passed=8,
    failed=2,
    status="failed",
)

SAMPLE_VALIDATION_ERROR = ValidateResponse(
    tests_run=0,
    passed=0,
    failed=0,
    status="error",
)


# ---------------------------------------------------------------------------
# Field-copying tests
# ---------------------------------------------------------------------------


class TestFieldCopying:
    def test_issue_copied(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.issue == SAMPLE_INVESTIGATION.issue

    def test_relevant_files_preserved(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.relevant_files == SAMPLE_INVESTIGATION.relevant_files

    def test_root_cause_preserved(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.root_cause == SAMPLE_INVESTIGATION.root_cause

    def test_suggested_fix_preserved(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.suggested_fix == SAMPLE_INVESTIGATION.suggested_fix

    def test_test_generated_maps_to_regression_test(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.regression_test == SAMPLE_INVESTIGATION.test_generated

    def test_confidence_preserved(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.confidence == pytest.approx(SAMPLE_INVESTIGATION.confidence)

    def test_tests_run_preserved(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.tests_run == SAMPLE_VALIDATION_PASSED.tests_run

    def test_passed_count_preserved(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert report.passed == SAMPLE_VALIDATION_PASSED.passed

    def test_failed_count_preserved(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_FAILED)
        assert report.failed == SAMPLE_VALIDATION_FAILED.failed

    def test_validation_status_preserved(self):
        for val in (SAMPLE_VALIDATION_PASSED, SAMPLE_VALIDATION_FAILED, SAMPLE_VALIDATION_ERROR):
            report = build_engineering_report(SAMPLE_INVESTIGATION, val)
            assert report.validation_status == val.status


# ---------------------------------------------------------------------------
# Outcome language tests
# ---------------------------------------------------------------------------


class TestOutcomeLanguage:
    def test_passed_outcome_mentions_all_tests_passed(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        outcome = report.outcome.lower()
        # Must convey success
        assert "passed" in outcome

    def test_passed_outcome_does_not_claim_repair_applied(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        outcome = report.outcome.lower()
        # Must not falsely claim a repair was physically applied
        assert "repair has been applied" not in outcome
        assert "fix has been applied" not in outcome
        assert "bug is fixed" not in outcome
        assert "bug has been fixed" not in outcome

    def test_passed_outcome_does_not_claim_test_file_created(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        outcome = report.outcome.lower()
        # Must not falsely claim a regression-test file was physically created.
        # Acceptable: negated language such as "a regression test file has not been created"
        # or "does not confirm … a regression test file has been created".
        # Not acceptable: affirmative claims that a file was created.
        assert "a regression test file has been created" not in outcome or "not confirm" in outcome
        assert "we created a regression test" not in outcome
        assert "regression test was created" not in outcome

    def test_failed_outcome_conveys_failure(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_FAILED)
        outcome = report.outcome.lower()
        assert "failed" in outcome

    def test_failed_outcome_mentions_further_action_needed(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_FAILED)
        outcome = report.outcome.lower()
        # Should indicate more work is needed
        assert any(
            phrase in outcome
            for phrase in ("required", "repair", "further", "investigation")
        )

    def test_error_outcome_conveys_environment_problem(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_ERROR)
        outcome = report.outcome.lower()
        assert "error" in outcome

    def test_error_outcome_no_false_conclusion(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_ERROR)
        outcome = report.outcome.lower()
        assert "all tests passed" not in outcome
        assert "tests failed" not in outcome


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_inputs_same_output(self):
        r1 = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        r2 = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert r1.model_dump() == r2.model_dump()

    def test_different_status_different_outcome(self):
        r_passed = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        r_failed = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_FAILED)
        r_error = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_ERROR)
        # All three outcomes must differ
        assert r_passed.outcome != r_failed.outcome
        assert r_passed.outcome != r_error.outcome
        assert r_failed.outcome != r_error.outcome


# ---------------------------------------------------------------------------
# Input immutability tests
# ---------------------------------------------------------------------------


class TestInputImmutability:
    def test_investigation_not_mutated(self):
        original_issue = SAMPLE_INVESTIGATION.issue
        original_files = list(SAMPLE_INVESTIGATION.relevant_files)
        build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert SAMPLE_INVESTIGATION.issue == original_issue
        assert SAMPLE_INVESTIGATION.relevant_files == original_files

    def test_validation_not_mutated(self):
        original_status = SAMPLE_VALIDATION_PASSED.status
        original_tests_run = SAMPLE_VALIDATION_PASSED.tests_run
        build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        assert SAMPLE_VALIDATION_PASSED.status == original_status
        assert SAMPLE_VALIDATION_PASSED.tests_run == original_tests_run

    def test_relevant_files_is_independent_copy(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        # Modifying the report's list does not affect the investigation's list
        original_len = len(SAMPLE_INVESTIGATION.relevant_files)
        report.relevant_files.append("injected.py")
        assert len(SAMPLE_INVESTIGATION.relevant_files) == original_len


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_engineering_report_serializes_to_dict(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        data = report.model_dump()
        assert isinstance(data, dict)

    def test_serialization_contains_all_expected_keys(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        data = report.model_dump()
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

    def test_serialization_values_correct_types(self):
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        data = report.model_dump()
        assert isinstance(data["issue"], str)
        assert isinstance(data["relevant_files"], list)
        assert isinstance(data["root_cause"], str)
        assert isinstance(data["suggested_fix"], str)
        assert isinstance(data["regression_test"], str)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["tests_run"], int)
        assert isinstance(data["passed"], int)
        assert isinstance(data["failed"], int)
        assert isinstance(data["validation_status"], str)
        assert isinstance(data["outcome"], str)

    def test_outcome_is_non_empty_string(self):
        for val in (SAMPLE_VALIDATION_PASSED, SAMPLE_VALIDATION_FAILED, SAMPLE_VALIDATION_ERROR):
            report = build_engineering_report(SAMPLE_INVESTIGATION, val)
            assert isinstance(report.outcome, str)
            assert len(report.outcome) > 0


# ---------------------------------------------------------------------------
# Existing schema contract unchanged tests
# ---------------------------------------------------------------------------


class TestExistingContractsUnchanged:
    """Verify InvestigateResponse and ValidateResponse field sets are not altered."""

    def test_investigate_response_field_set(self):
        resp = InvestigateResponse(
            issue="test",
            relevant_files=[],
            root_cause="cause",
            suggested_fix="fix",
            test_generated="test rec",
            confidence=0.5,
        )
        data = resp.model_dump()
        assert set(data.keys()) == {
            "issue",
            "relevant_files",
            "root_cause",
            "suggested_fix",
            "test_generated",
            "confidence",
        }

    def test_validate_response_field_set(self):
        resp = ValidateResponse(tests_run=1, passed=1, failed=0, status="passed")
        data = resp.model_dump()
        assert set(data.keys()) == {"tests_run", "passed", "failed", "status"}

    def test_engineering_report_does_not_use_test_generated_field(self):
        """EngineeringReport uses regression_test, not test_generated."""
        report = build_engineering_report(SAMPLE_INVESTIGATION, SAMPLE_VALIDATION_PASSED)
        data = report.model_dump()
        assert "test_generated" not in data
        assert "regression_test" in data
