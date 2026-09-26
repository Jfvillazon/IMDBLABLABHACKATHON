"""
Tests for POST /api/investigate

Covers the 11 required test cases:

 1. POST /api/investigate returns HTTP 200 for a valid request.
 2. Response matches InvestigateResponse schema.
 3. Existing Investigation Engine is actually invoked.
 4. Primary checkout/missing-quantity scenario works through HTTP.
 5. Empty issue is rejected appropriately.
 6. Invalid repository path is handled as an HTTP error, not an uncaught exception.
 7. Unknown issue still returns the engine fallback successfully.
 8. Response confidence remains within [0.0, 1.0].
 9. No absolute repository paths leak unexpectedly.
10. GET /health still works.
11. All pre-existing tests still pass (verified by running the full suite).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.main import app
from backend.models.schemas import InvestigateResponse

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(*files: tuple[str, str]) -> tempfile.TemporaryDirectory:
    """
    Create a temporary directory containing the given (relative_path, content) files.
    Returns the TemporaryDirectory object; caller is responsible for cleanup.
    """
    tmp = tempfile.TemporaryDirectory()
    for rel_path, content in files:
        target = Path(tmp.name) / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp


_CHECKOUT_ISSUE = "Checkout crashes when quantity is missing."

_CHECKOUT_FILE_CONTENT = (
    "def checkout(cart, quantity):\n"
    "    total = cart['price'] * quantity\n"
    "    return total\n"
)

# ---------------------------------------------------------------------------
# Test 1 — HTTP 200 for a valid request
# ---------------------------------------------------------------------------


class TestHttp200ValidRequest:
    def setup_method(self):
        self.tmp = _make_repo(("checkout.py", _CHECKOUT_FILE_CONTENT))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_returns_200(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert response.status_code == 200

    def test_content_type_is_json(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert "application/json" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Test 2 — Response matches InvestigateResponse schema
# ---------------------------------------------------------------------------


class TestResponseMatchesSchema:
    def setup_method(self):
        self.tmp = _make_repo(("checkout.py", _CHECKOUT_FILE_CONTENT))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_response_has_required_fields(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        data = response.json()
        required_keys = {
            "issue",
            "relevant_files",
            "root_cause",
            "suggested_fix",
            "test_generated",
            "confidence",
        }
        assert required_keys.issubset(set(data.keys()))

    def test_response_validates_against_pydantic_schema(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        # Should not raise — all fields must be present and correctly typed.
        parsed = InvestigateResponse(**response.json())
        assert parsed.issue == _CHECKOUT_ISSUE

    def test_relevant_files_is_list(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert isinstance(response.json()["relevant_files"], list)

    def test_test_generated_is_string(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert isinstance(response.json()["test_generated"], str)

    def test_confidence_is_float(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert isinstance(response.json()["confidence"], float)


# ---------------------------------------------------------------------------
# Test 3 — Investigation Engine is actually invoked
# ---------------------------------------------------------------------------


class TestEngineIsInvoked:
    def setup_method(self):
        self.tmp = _make_repo(("checkout.py", _CHECKOUT_FILE_CONTENT))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_engine_called_once(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            with patch(
                "backend.api.investigate.investigate_issue",
                wraps=__import__(
                    "backend.services.investigation", fromlist=["investigate_issue"]
                ).investigate_issue,
            ) as mock_engine:
                client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
                mock_engine.assert_called_once()

    def test_engine_receives_correct_issue(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            with patch(
                "backend.api.investigate.investigate_issue",
                wraps=__import__(
                    "backend.services.investigation", fromlist=["investigate_issue"]
                ).investigate_issue,
            ) as mock_engine:
                client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
                call_kwargs = mock_engine.call_args
                assert call_kwargs.kwargs["issue"] == _CHECKOUT_ISSUE or (
                    call_kwargs.args and call_kwargs.args[0] == _CHECKOUT_ISSUE
                )


# ---------------------------------------------------------------------------
# Test 4 — Checkout / missing-quantity scenario works through HTTP
# ---------------------------------------------------------------------------


class TestCheckoutScenarioThroughHttp:
    def setup_method(self):
        self.tmp = _make_repo(
            ("checkout.py", _CHECKOUT_FILE_CONTENT),
            ("validation.py", "def validate_quantity(qty):\n    pass\n"),
        )

    def teardown_method(self):
        self.tmp.cleanup()

    def test_checkout_issue_returns_200(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert response.status_code == 200

    def test_checkout_root_cause_mentions_quantity(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        root_cause = response.json()["root_cause"].lower()
        assert "quantity" in root_cause

    def test_checkout_suggested_fix_mentions_validate(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        suggested_fix = response.json()["suggested_fix"].lower()
        assert "validat" in suggested_fix

    def test_checkout_issue_echoed_in_response(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert response.json()["issue"] == _CHECKOUT_ISSUE

    def test_checkout_confidence_is_high(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        assert response.json()["confidence"] >= 0.5


# ---------------------------------------------------------------------------
# Test 5 — Empty issue is rejected appropriately
# ---------------------------------------------------------------------------


class TestEmptyIssueRejection:
    """
    InvestigateRequest has min_length=1, so Pydantic rejects empty strings
    before the endpoint body is reached → FastAPI returns 422.
    """

    def test_empty_string_returns_422(self):
        response = client.post("/api/investigate", json={"issue": ""})
        assert response.status_code == 422

    def test_missing_issue_field_returns_422(self):
        response = client.post("/api/investigate", json={})
        assert response.status_code == 422

    def test_empty_response_is_not_500(self):
        response = client.post("/api/investigate", json={"issue": ""})
        assert response.status_code != 500

    def test_whitespace_only_issue_rejected_by_service(self):
        """
        Whitespace-only strings pass Pydantic's min_length=1 check but are
        caught by the service as an empty issue → endpoint must return 422
        (not 500).
        """
        with patch(
            "backend.api.investigate._resolve_repo_path",
            return_value=tempfile.mkdtemp(),
        ) as _patched:
            response = client.post("/api/investigate", json={"issue": "   "})
        assert response.status_code == 422
        assert response.status_code != 500


# ---------------------------------------------------------------------------
# Test 6 — Invalid repository path handled as HTTP error, not raw exception
# ---------------------------------------------------------------------------


class TestInvalidRepositoryPath:
    def test_nonexistent_path_returns_422(self):
        with patch(
            "backend.api.investigate._resolve_repo_path",
            return_value="/nonexistent/path/that/does/not/exist",
        ):
            response = client.post(
                "/api/investigate",
                json={"issue": _CHECKOUT_ISSUE},
            )
        assert response.status_code == 422

    def test_nonexistent_path_not_500(self):
        with patch(
            "backend.api.investigate._resolve_repo_path",
            return_value="/nonexistent/path/that/does/not/exist",
        ):
            response = client.post(
                "/api/investigate",
                json={"issue": _CHECKOUT_ISSUE},
            )
        assert response.status_code != 500

    def test_nonexistent_path_returns_json(self):
        with patch(
            "backend.api.investigate._resolve_repo_path",
            return_value="/nonexistent/path/that/does/not/exist",
        ):
            response = client.post(
                "/api/investigate",
                json={"issue": _CHECKOUT_ISSUE},
            )
        # Must be JSON with a 'detail' key, not a raw Python traceback.
        assert "detail" in response.json()

    def test_file_path_not_directory_returns_422(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            file_path = f.name
        try:
            with patch(
                "backend.api.investigate._resolve_repo_path",
                return_value=file_path,
            ):
                response = client.post(
                    "/api/investigate",
                    json={"issue": _CHECKOUT_ISSUE},
                )
            assert response.status_code == 422
        finally:
            import os
            os.unlink(file_path)


# ---------------------------------------------------------------------------
# Test 7 — Unknown issue returns engine fallback successfully
# ---------------------------------------------------------------------------


class TestUnknownIssueFallback:
    def setup_method(self):
        self.tmp = _make_repo(("app.py", "print('hello')\n"))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_unknown_issue_returns_200(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post(
                "/api/investigate",
                json={"issue": "Something completely unrelated and unrecognised xyzzy"},
            )
        assert response.status_code == 200

    def test_unknown_issue_has_nonempty_root_cause(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post(
                "/api/investigate",
                json={"issue": "Something completely unrelated and unrecognised xyzzy"},
            )
        assert len(response.json()["root_cause"]) > 0

    def test_unknown_issue_validates_against_schema(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post(
                "/api/investigate",
                json={"issue": "Something completely unrelated and unrecognised xyzzy"},
            )
        # Should not raise — schema must be satisfied even for the fallback.
        InvestigateResponse(**response.json())


# ---------------------------------------------------------------------------
# Test 8 — Confidence remains within [0.0, 1.0]
# ---------------------------------------------------------------------------


class TestConfidenceBounds:
    def setup_method(self):
        self.tmp = _make_repo(("checkout.py", _CHECKOUT_FILE_CONTENT))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_high_confidence_in_range(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        conf = response.json()["confidence"]
        assert 0.0 <= conf <= 1.0

    def test_low_confidence_in_range(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post(
                "/api/investigate",
                json={"issue": "Something completely unrelated and unrecognised xyzzy"},
            )
        conf = response.json()["confidence"]
        assert 0.0 <= conf <= 1.0

    def test_confidence_never_exceeds_one(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            for issue in [
                _CHECKOUT_ISSUE,
                "auth failure on login",
                "payment processing error",
                "configuration missing env variable",
                "unknown xyzzy issue",
            ]:
                response = client.post("/api/investigate", json={"issue": issue})
                assert response.json()["confidence"] <= 1.0, f"Exceeded 1.0 for: {issue}"

    def test_confidence_never_below_zero(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
            assert response.json()["confidence"] >= 0.0


# ---------------------------------------------------------------------------
# Test 9 — No absolute repository paths leak unexpectedly
# ---------------------------------------------------------------------------


class TestNoAbsolutePathLeak:
    def setup_method(self):
        self.tmp = _make_repo(("checkout.py", _CHECKOUT_FILE_CONTENT))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_relevant_files_are_relative(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        for path in response.json()["relevant_files"]:
            assert not path.startswith("/"), f"Absolute path leaked: {path!r}"

    def test_repo_root_not_in_relevant_files(self):
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        for path in response.json()["relevant_files"]:
            assert self.tmp.name not in path, (
                f"Absolute repo root leaked in path: {path!r}"
            )

    def test_tmp_dir_prefix_not_in_response_body(self):
        """No field in the response should contain the temporary directory's absolute path."""
        with patch("backend.api.investigate._resolve_repo_path", return_value=self.tmp.name):
            response = client.post("/api/investigate", json={"issue": _CHECKOUT_ISSUE})
        raw_body = response.text
        assert self.tmp.name not in raw_body, (
            f"Temporary repo path {self.tmp.name!r} leaked into response body."
        )


# ---------------------------------------------------------------------------
# Test 10 — GET /health still works
# ---------------------------------------------------------------------------


class TestHealthStillWorks:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_correct_body(self):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}

    def test_health_unaffected_by_investigate_router(self):
        """Registering the investigate router must not break /health."""
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json() == {"status": "ok"}
