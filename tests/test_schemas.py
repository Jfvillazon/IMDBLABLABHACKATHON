"""
Tests for backend/models/schemas.py

Covers:
  - valid model construction
  - expected serialization (field names / values)
  - required-field validation (missing fields raise ValidationError)
  - invalid input rejection (type/range violations raise ValidationError)
"""

import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    InvestigateRequest,
    InvestigateResponse,
    ValidateResponse,
)


# ---------------------------------------------------------------------------
# InvestigateRequest
# ---------------------------------------------------------------------------


class TestInvestigateRequest:
    def test_valid_construction(self):
        req = InvestigateRequest(issue="Checkout crashes on missing quantity.")
        assert req.issue == "Checkout crashes on missing quantity."

    def test_serialization(self):
        req = InvestigateRequest(issue="Some bug")
        data = req.model_dump()
        assert data == {"issue": "Some bug"}

    def test_missing_issue_raises(self):
        with pytest.raises(ValidationError):
            InvestigateRequest()

    def test_empty_issue_raises(self):
        with pytest.raises(ValidationError):
            InvestigateRequest(issue="")

    def test_extra_fields_ignored(self):
        # Pydantic v2 default: extra fields are ignored, not an error
        req = InvestigateRequest(issue="bug", unexpected_field="x")
        assert req.issue == "bug"


# ---------------------------------------------------------------------------
# InvestigateResponse
# ---------------------------------------------------------------------------


VALID_INVESTIGATE_RESPONSE = dict(
    issue="Checkout crashes on missing quantity.",
    relevant_files=["checkout.py", "validation.py"],
    root_cause="Input is used before validation.",
    suggested_fix="Validate request before processing.",
    test_generated="Add a regression test for missing quantity input.",
    confidence=0.95,
)


class TestInvestigateResponse:
    def test_valid_construction(self):
        resp = InvestigateResponse(**VALID_INVESTIGATE_RESPONSE)
        assert resp.issue == "Checkout crashes on missing quantity."
        assert resp.relevant_files == ["checkout.py", "validation.py"]
        assert resp.root_cause == "Input is used before validation."
        assert resp.suggested_fix == "Validate request before processing."
        assert resp.test_generated == "Add a regression test for missing quantity input."
        assert resp.confidence == pytest.approx(0.95)

    def test_serialization_keys(self):
        resp = InvestigateResponse(**VALID_INVESTIGATE_RESPONSE)
        data = resp.model_dump()
        assert set(data.keys()) == {
            "issue",
            "relevant_files",
            "root_cause",
            "suggested_fix",
            "test_generated",
            "confidence",
        }

    def test_serialization_values(self):
        resp = InvestigateResponse(**VALID_INVESTIGATE_RESPONSE)
        data = resp.model_dump()
        assert data["confidence"] == pytest.approx(0.95)
        assert isinstance(data["test_generated"], str)
        assert isinstance(data["relevant_files"], list)

    # --- confidence boundary ---

    def test_confidence_zero_is_valid(self):
        resp = InvestigateResponse(**{**VALID_INVESTIGATE_RESPONSE, "confidence": 0.0})
        assert resp.confidence == 0.0

    def test_confidence_one_is_valid(self):
        resp = InvestigateResponse(**{**VALID_INVESTIGATE_RESPONSE, "confidence": 1.0})
        assert resp.confidence == 1.0

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            InvestigateResponse(**{**VALID_INVESTIGATE_RESPONSE, "confidence": 1.01})

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            InvestigateResponse(**{**VALID_INVESTIGATE_RESPONSE, "confidence": -0.01})

    # --- test_generated is str, not bool ---

    def test_test_generated_is_string(self):
        resp = InvestigateResponse(**VALID_INVESTIGATE_RESPONSE)
        assert isinstance(resp.test_generated, str)

    def test_test_generated_bool_rejected(self):
        # Pydantic v2 does NOT coerce bool to str — a bare True must raise ValidationError.
        with pytest.raises(ValidationError):
            InvestigateResponse(**{**VALID_INVESTIGATE_RESPONSE, "test_generated": True})

    # --- required fields ---

    def test_missing_issue_raises(self):
        data = {k: v for k, v in VALID_INVESTIGATE_RESPONSE.items() if k != "issue"}
        with pytest.raises(ValidationError):
            InvestigateResponse(**data)

    def test_missing_relevant_files_raises(self):
        data = {k: v for k, v in VALID_INVESTIGATE_RESPONSE.items() if k != "relevant_files"}
        with pytest.raises(ValidationError):
            InvestigateResponse(**data)

    def test_missing_root_cause_raises(self):
        data = {k: v for k, v in VALID_INVESTIGATE_RESPONSE.items() if k != "root_cause"}
        with pytest.raises(ValidationError):
            InvestigateResponse(**data)

    def test_missing_suggested_fix_raises(self):
        data = {k: v for k, v in VALID_INVESTIGATE_RESPONSE.items() if k != "suggested_fix"}
        with pytest.raises(ValidationError):
            InvestigateResponse(**data)

    def test_missing_test_generated_raises(self):
        data = {k: v for k, v in VALID_INVESTIGATE_RESPONSE.items() if k != "test_generated"}
        with pytest.raises(ValidationError):
            InvestigateResponse(**data)

    def test_missing_confidence_raises(self):
        data = {k: v for k, v in VALID_INVESTIGATE_RESPONSE.items() if k != "confidence"}
        with pytest.raises(ValidationError):
            InvestigateResponse(**data)

    def test_relevant_files_empty_list_is_valid(self):
        resp = InvestigateResponse(**{**VALID_INVESTIGATE_RESPONSE, "relevant_files": []})
        assert resp.relevant_files == []

    def test_confidence_non_numeric_raises(self):
        with pytest.raises(ValidationError):
            InvestigateResponse(**{**VALID_INVESTIGATE_RESPONSE, "confidence": "high"})


# ---------------------------------------------------------------------------
# ValidateResponse
# ---------------------------------------------------------------------------


VALID_VALIDATE_RESPONSE = dict(
    tests_run=12,
    passed=12,
    failed=0,
    status="passed",
)


class TestValidateResponse:
    def test_valid_passed(self):
        resp = ValidateResponse(**VALID_VALIDATE_RESPONSE)
        assert resp.tests_run == 12
        assert resp.passed == 12
        assert resp.failed == 0
        assert resp.status == "passed"

    def test_valid_failed(self):
        resp = ValidateResponse(tests_run=5, passed=3, failed=2, status="failed")
        assert resp.status == "failed"
        assert resp.failed == 2

    def test_valid_error(self):
        resp = ValidateResponse(tests_run=0, passed=0, failed=0, status="error")
        assert resp.status == "error"

    def test_serialization(self):
        resp = ValidateResponse(**VALID_VALIDATE_RESPONSE)
        data = resp.model_dump()
        assert data == {"tests_run": 12, "passed": 12, "failed": 0, "status": "passed"}

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            ValidateResponse(**{**VALID_VALIDATE_RESPONSE, "status": "unknown"})

    def test_negative_tests_run_raises(self):
        with pytest.raises(ValidationError):
            ValidateResponse(**{**VALID_VALIDATE_RESPONSE, "tests_run": -1})

    def test_negative_passed_raises(self):
        with pytest.raises(ValidationError):
            ValidateResponse(**{**VALID_VALIDATE_RESPONSE, "passed": -1})

    def test_negative_failed_raises(self):
        with pytest.raises(ValidationError):
            ValidateResponse(**{**VALID_VALIDATE_RESPONSE, "failed": -1})

    def test_missing_status_raises(self):
        data = {k: v for k, v in VALID_VALIDATE_RESPONSE.items() if k != "status"}
        with pytest.raises(ValidationError):
            ValidateResponse(**data)

    def test_missing_tests_run_raises(self):
        data = {k: v for k, v in VALID_VALIDATE_RESPONSE.items() if k != "tests_run"}
        with pytest.raises(ValidationError):
            ValidateResponse(**data)

    def test_zero_counts_are_valid(self):
        resp = ValidateResponse(tests_run=0, passed=0, failed=0, status="passed")
        assert resp.tests_run == 0
