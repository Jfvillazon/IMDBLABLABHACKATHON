"""Integration tests verifying that the REAL backend.main application exposes
all four required endpoints with correct response shapes.

These tests use backend.main.app directly — no isolated sub-app — so they
validate the full routing table after Member 2's analyze router was registered.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_endpoint_present() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /api/analyze
# ---------------------------------------------------------------------------

def test_analyze_endpoint_present(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """POST /api/analyze returns 200 using a controlled temp repo."""
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path))
    response = client.post("/api/analyze")
    assert response.status_code == 200


def test_analyze_response_contract(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Response has exactly the five-field contract with correct types."""
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path))
    body = client.post("/api/analyze").json()
    assert set(body.keys()) == {
        "repository", "files_analyzed", "languages", "health_score", "findings"
    }
    assert isinstance(body["repository"], str)
    assert isinstance(body["files_analyzed"], int) and body["files_analyzed"] >= 0
    assert isinstance(body["languages"], list)
    assert isinstance(body["health_score"], int)
    assert 0 <= body["health_score"] <= 100
    assert isinstance(body["findings"], list)


def test_analyze_findings_contract(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Each finding must have the eight required fields with correct types."""
    (tmp_path / "app.py").write_text(
        'API_KEY = "FAKE_DEMO_KEY_NOT_REAL"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path))
    body = client.post("/api/analyze").json()
    assert len(body["findings"]) >= 1, "expected at least one security finding"
    for finding in body["findings"]:
        assert set(finding.keys()) == {
            "id", "category", "severity", "title", "file", "line",
            "description", "recommendation",
        }
        assert finding["severity"] in {"high", "medium", "low"}
        assert isinstance(finding["id"], str)
        assert isinstance(finding["category"], str)
        assert isinstance(finding["title"], str)
        assert isinstance(finding["description"], str)
        assert isinstance(finding["recommendation"], str)
        assert finding["line"] is None or isinstance(finding["line"], int)


def test_analyze_against_sample_repo() -> None:
    """Analyze the controlled sample_repo and verify the contract (no monkeypatch)."""
    response = client.post("/api/analyze")
    # The sample_repo exists; analysis must succeed.
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "repository", "files_analyzed", "languages", "health_score", "findings"
    }
    assert body["files_analyzed"] >= 1


def test_analyze_ignores_client_supplied_path(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Client-supplied JSON body must NOT change the analyzed path."""
    (tmp_path / "safe.py").write_text("pass\n", encoding="utf-8")
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path))
    body_with_path = client.post("/api/analyze", json={"path": "/etc"}).json()
    assert body_with_path["repository"] == tmp_path.name


# ---------------------------------------------------------------------------
# POST /api/investigate
# ---------------------------------------------------------------------------

def test_investigate_endpoint_present() -> None:
    response = client.post(
        "/api/investigate",
        json={"repository": "test-repo", "issue": "items missing from checkout"},
    )
    assert response.status_code == 200


def test_investigate_response_contract() -> None:
    response = client.post(
        "/api/investigate",
        json={"repository": "test-repo", "issue": "items missing from checkout"},
    )
    body = response.json()
    # Must include confidence as a float in [0, 1]
    assert "confidence" in body
    assert isinstance(body["confidence"], float)
    assert 0.0 <= body["confidence"] <= 1.0
    # test_generated must be a string
    assert "test_generated" in body
    assert isinstance(body["test_generated"], str)


# ---------------------------------------------------------------------------
# POST /api/validate
# ---------------------------------------------------------------------------

def test_validate_endpoint_present() -> None:
    response = client.post(
        "/api/validate",
        json={"repository": "test-repo", "test_suite": "pytest"},
    )
    assert response.status_code in {200, 422}  # 422 if payload shape differs


def test_validate_endpoint_reachable() -> None:
    """Endpoint must exist on the real app (not 404)."""
    response = client.post("/api/validate", json={})
    assert response.status_code != 404


# ---------------------------------------------------------------------------
# Routing table sanity
# ---------------------------------------------------------------------------

def test_all_four_routes_registered() -> None:
    """Confirm the live routing table contains all four required paths."""
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/health" in paths
    assert "/api/analyze" in paths
    assert "/api/investigate" in paths
    assert "/api/validate" in paths
