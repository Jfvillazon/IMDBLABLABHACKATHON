"""
Tests for POST /api/validate

Covers:
  API:
  1.  Endpoint exists (POST /api/validate returns a recognised HTTP status)
  2.  Correct HTTP method — GET is rejected (405)
  3.  Successful response structure matches ValidateResponse schema
  4.  Correct ValidateResponse serialisation (field names, types)
  5.  Failed-test scenario is handled correctly (status="failed", not 500)
  6.  Service-level execution error is handled predictably (status="error")
  7.  GET /health still works after adding the validate router
  8.  POST /api/investigate still works after adding the validate router
  9.  Passing scenario — full field verification
  10. No request body is required (POST with empty body succeeds)
  11. Response body never contains unexpected status values
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import ValidateResponse

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASSING_TEST = "def test_always_passes():\n    assert 1 + 1 == 2\n"
_FAILING_TEST = (
    "def test_always_fails():\n"
    "    assert False, 'intentional failure'\n"
)


def _make_test_dir(*files: tuple[str, str]) -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory()
    for rel_path, content in files:
        target = Path(tmp.name) / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp


# ---------------------------------------------------------------------------
# Test 1 — Endpoint exists
# ---------------------------------------------------------------------------


class TestEndpointExists:
    def test_post_validate_returns_recognised_status(self):
        """POST /api/validate must return a recognised HTTP status (not 404)."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("backend.api.validate._resolve_test_path", return_value=tmp):
                response = client.post("/api/validate")
        assert response.status_code != 404

    def test_post_validate_not_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("backend.api.validate._resolve_test_path", return_value=tmp):
                response = client.post("/api/validate")
        assert response.status_code != 404

    def test_post_validate_returns_200(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("backend.api.validate._resolve_test_path", return_value=tmp):
                response = client.post("/api/validate")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Test 2 — Correct HTTP method enforced (GET → 405)
# ---------------------------------------------------------------------------


class TestCorrectHttpMethod:
    def test_get_is_not_allowed(self):
        response = client.get("/api/validate")
        assert response.status_code == 405

    def test_put_is_not_allowed(self):
        response = client.put("/api/validate")
        assert response.status_code in {404, 405}

    def test_delete_is_not_allowed(self):
        response = client.delete("/api/validate")
        assert response.status_code in {404, 405}


# ---------------------------------------------------------------------------
# Test 3 — Response structure matches ValidateResponse schema
# ---------------------------------------------------------------------------


class TestResponseStructure:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_passing.py", _PASSING_TEST))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_response_has_required_fields(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        data = response.json()
        required_keys = {"tests_run", "passed", "failed", "status"}
        assert required_keys.issubset(set(data.keys()))

    def test_response_validates_against_pydantic_schema(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        # Should not raise — all fields must be present and correctly typed.
        parsed = ValidateResponse(**response.json())
        assert parsed.status in {"passed", "failed", "error"}

    def test_status_field_is_string(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert isinstance(response.json()["status"], str)

    def test_tests_run_is_int(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert isinstance(response.json()["tests_run"], int)

    def test_passed_is_int(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert isinstance(response.json()["passed"], int)

    def test_failed_is_int(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert isinstance(response.json()["failed"], int)


# ---------------------------------------------------------------------------
# Test 4 — Correct ValidateResponse serialisation
# ---------------------------------------------------------------------------


class TestValidateResponseSerialisation:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_passing.py", _PASSING_TEST))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_content_type_is_json(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert "application/json" in response.headers["content-type"]

    def test_passing_scenario_serialises_correctly(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        data = response.json()
        assert data["status"] == "passed"
        assert data["passed"] >= 1
        assert data["failed"] == 0
        assert data["tests_run"] == data["passed"] + data["failed"]

    def test_no_extra_unexpected_fields(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        data = response.json()
        allowed_keys = {"tests_run", "passed", "failed", "status"}
        assert set(data.keys()) == allowed_keys


# ---------------------------------------------------------------------------
# Test 5 — Failed-test scenario is handled correctly (not a 500)
# ---------------------------------------------------------------------------


class TestFailedTestScenario:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_failing.py", _FAILING_TEST))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_failing_tests_returns_200(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert response.status_code == 200

    def test_failing_tests_status_is_failed(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert response.json()["status"] == "failed"

    def test_failing_tests_not_500(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert response.status_code != 500

    def test_failing_tests_response_validates_against_schema(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        ValidateResponse(**response.json())  # must not raise

    def test_failing_tests_failed_count_nonzero(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert response.json()["failed"] >= 1


# ---------------------------------------------------------------------------
# Test 6 — Service-level execution error is handled predictably
# ---------------------------------------------------------------------------


class TestServiceExecutionError:
    def test_missing_path_returns_200(self):
        with patch(
            "backend.api.validate._resolve_test_path",
            return_value="/nonexistent/xyzzy/path",
        ):
            response = client.post("/api/validate")
        assert response.status_code == 200

    def test_missing_path_status_is_error(self):
        with patch(
            "backend.api.validate._resolve_test_path",
            return_value="/nonexistent/xyzzy/path",
        ):
            response = client.post("/api/validate")
        assert response.json()["status"] == "error"

    def test_missing_path_not_500(self):
        with patch(
            "backend.api.validate._resolve_test_path",
            return_value="/nonexistent/xyzzy/path",
        ):
            response = client.post("/api/validate")
        assert response.status_code != 500

    def test_missing_path_response_validates_against_schema(self):
        with patch(
            "backend.api.validate._resolve_test_path",
            return_value="/nonexistent/xyzzy/path",
        ):
            response = client.post("/api/validate")
        ValidateResponse(**response.json())  # must not raise

    def test_missing_path_counts_are_zero(self):
        with patch(
            "backend.api.validate._resolve_test_path",
            return_value="/nonexistent/xyzzy/path",
        ):
            response = client.post("/api/validate")
        data = response.json()
        assert data["tests_run"] == 0
        assert data["passed"] == 0
        assert data["failed"] == 0


# ---------------------------------------------------------------------------
# Test 7 — GET /health still works
# ---------------------------------------------------------------------------


class TestHealthStillWorks:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_correct_body(self):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}

    def test_health_unaffected_by_validate_router(self):
        """Registering the validate router must not break /health."""
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Test 8 — POST /api/investigate still works
# ---------------------------------------------------------------------------


class TestInvestigateStillWorks:
    def setup_method(self):
        self.tmp = tempfile.TemporaryDirectory()
        Path(self.tmp.name, "checkout.py").write_text(
            "def checkout(cart, quantity):\n    total = cart['price'] * quantity\n    return total\n"
        )

    def teardown_method(self):
        self.tmp.cleanup()

    def test_investigate_returns_200(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post(
                "/api/investigate",
                json={"issue": "Checkout crashes when quantity is missing."},
            )
        assert response.status_code == 200

    def test_investigate_response_is_valid(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post(
                "/api/investigate",
                json={"issue": "Checkout crashes when quantity is missing."},
            )
        data = response.json()
        required_keys = {"issue", "relevant_files", "root_cause", "suggested_fix", "test_generated", "confidence"}
        assert required_keys.issubset(set(data.keys()))


# ---------------------------------------------------------------------------
# Test 9 — Passing scenario full field verification
# ---------------------------------------------------------------------------


class TestPassingScenarioFullVerification:
    def setup_method(self):
        self.tmp = _make_test_dir(
            ("test_a.py", "def test_one():\n    assert True\n"),
            ("test_b.py", "def test_two():\n    assert True\n"),
        )

    def teardown_method(self):
        self.tmp.cleanup()

    def test_tests_run_matches_sum(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        data = response.json()
        assert data["tests_run"] == data["passed"] + data["failed"]

    def test_status_is_passed_when_all_pass(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert response.json()["status"] == "passed"

    def test_failed_is_zero_when_all_pass(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert response.json()["failed"] == 0

    def test_passed_equals_tests_run_when_all_pass(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        data = response.json()
        assert data["passed"] == data["tests_run"]


# ---------------------------------------------------------------------------
# Test 10 — No request body required
# ---------------------------------------------------------------------------


class TestNoRequestBodyRequired:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_x.py", _PASSING_TEST))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_post_with_no_body_succeeds(self):
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate")
        assert response.status_code == 200

    def test_post_with_empty_json_body_succeeds(self):
        """Optional: if a body is accidentally sent, it should still work."""
        with patch("backend.api.validate._resolve_test_path", return_value=self.tmp.name):
            response = client.post("/api/validate", json={})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Test 11 — status is always one of the Literal values
# ---------------------------------------------------------------------------


class TestStatusLiteralValues:
    _VALID_STATUSES = {"passed", "failed", "error"}

    def test_status_is_valid_literal_for_passing(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("backend.api.validate._resolve_test_path", return_value=tmp):
                response = client.post("/api/validate")
        assert response.json()["status"] in self._VALID_STATUSES

    def test_status_is_valid_literal_for_failing(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_FAILING_TEST)
            with patch("backend.api.validate._resolve_test_path", return_value=tmp):
                response = client.post("/api/validate")
        assert response.json()["status"] in self._VALID_STATUSES

    def test_status_is_valid_literal_for_error(self):
        with patch(
            "backend.api.validate._resolve_test_path",
            return_value="/nonexistent/xyzzy/path",
        ):
            response = client.post("/api/validate")
        assert response.json()["status"] in self._VALID_STATUSES
