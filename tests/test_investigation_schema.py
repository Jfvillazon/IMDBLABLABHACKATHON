"""Regression tests for the final approved investigation response contract."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.models.schemas import InvestigationResponse


VALID = {
    "issue": "Checkout crashes when quantity is missing.",
    "relevant_files": ["checkout.py"],
    "root_cause": "Input is used before validation.",
    "suggested_fix": "Validate quantity before processing.",
    "test_generated": "Add a regression test for missing quantity.",
    "confidence": 0.95,
}


def test_final_contract_accepts_string_test_and_float_confidence():
    response = InvestigationResponse(**VALID).model_dump()
    assert response == VALID
    assert isinstance(response["test_generated"], str)
    assert isinstance(response["confidence"], float)


@pytest.mark.parametrize("bad", [True, False, 1, None])
def test_bool_or_other_non_string_test_generated_is_rejected(bad):
    with pytest.raises(ValidationError):
        InvestigationResponse(**{**VALID, "test_generated": bad})


@pytest.mark.parametrize("bad", ["high", "medium", "low", -0.01, 1.01, float("nan")])
def test_confidence_must_be_a_finite_number_in_range(bad):
    with pytest.raises(ValidationError):
        InvestigationResponse(**{**VALID, "confidence": bad})


def test_boundaries_are_valid():
    assert InvestigationResponse(**{**VALID, "confidence": 0.0}).confidence == 0.0
    assert InvestigationResponse(**{**VALID, "confidence": 1.0}).confidence == 1.0


def test_schema_catches_unapproved_extra_fields():
    with pytest.raises(ValidationError):
        InvestigationResponse(**{**VALID, "test_created": True})
