"""Offline acceptance tests; no network, subprocess, real secrets, or Bobcoins."""
from __future__ import annotations

import json
import importlib
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.analyzers.architecture import summarize_architecture
from backend.analyzers.engine import analyze_repository, inspect_repository_structure
from backend.analyzers.health import calculate_health_score
from backend.analyzers.repository import scan_repository
from backend.api.analyze import router


def test_scanner_ignores_generated_and_hidden_content(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / ".env").write_text("REAL_SECRET=must_not_read", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignore.js").write_text("secret='x'", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    result = scan_repository(tmp_path)
    assert result["files_analyzed"] == 2
    assert result["languages"] == ["Python"]
    assert {p.relative_to(tmp_path).as_posix() for p in result["files"]} == {
        "app.py", "tests/test_app.py",
    }


def test_symlinks_never_leave_the_repo(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print(1)", encoding="utf-8")
    # Do not edit potentially existing files elsewhere in the real filesystem.
    unique_outside = tmp_path.parent / f"{tmp_path.name}-outside.py"
    unique_outside.write_text("PASSWORD='not-a-real-secret'", encoding="utf-8")
    try:
        (tmp_path / "linked.py").symlink_to(unique_outside)
        assert [p.name for p in scan_repository(tmp_path)["files"]] == ["app.py"]
    finally:
        unique_outside.unlink(missing_ok=True)


def test_detects_intentional_findings_without_leaking_secret(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Example repository", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        'API_KEY = "FAKE_DEMO_KEY_NOT_REAL"\n'
        'def process():\n'
        '    try:\n'
        '        return 1\n'
        '    except:\n'
        '        return 0\n', encoding="utf-8",
    )
    result = analyze_repository(tmp_path)
    assert result["repository"] == tmp_path.name
    assert result["files_analyzed"] == 1
    assert result["languages"] == ["Python"]
    categories = {f["category"] for f in result["findings"]}
    assert {"security", "testing", "error_handling"} <= categories
    assert result["health_score"] == 75  # high 10 + high 10 + medium 5
    assert "FAKE_DEMO_KEY_NOT_REAL" not in json.dumps(result)
    assert [f["id"] for f in result["findings"]] == ["F001", "F002", "F003"]


def test_score_is_clamped() -> None:
    high = {"severity": "high"}
    assert calculate_health_score([]) == 100
    assert calculate_health_score([high] * 20) == 0


def test_empty_repository_is_safe(tmp_path: Path) -> None:
    result = analyze_repository(tmp_path)
    assert result["files_analyzed"] == 0
    assert result["languages"] == []
    assert all(f["category"] != "testing" for f in result["findings"])
    assert 0 <= result["health_score"] <= 100


def test_syntax_error_does_not_abort_analysis(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("setup", encoding="utf-8")
    (tmp_path / "broken.py").write_text("def invalid(:\n", encoding="utf-8")
    assert any(f["title"] == "Python syntax error"
               for f in analyze_repository(tmp_path)["findings"])


def test_repeated_runs_produce_same_json(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("password = 'FAKE_ONLY_CREDENTIAL'\n", encoding="utf-8")
    assert analyze_repository(tmp_path) == analyze_repository(tmp_path)


def test_architecture_summary_detects_entry_points(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
    scan = scan_repository(tmp_path)
    summary = summarize_architecture(scan["root"], scan["files"])
    assert summary["entry_points"] == ["src/main.py"]
    assert summary["top_level_directories"] == ["src"]


def test_api_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path))
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).post("/api/analyze")
    assert response.status_code == 200
    assert set(response.json()) == {
        "repository", "files_analyzed", "languages", "health_score", "findings",
    }
    assert response.json()["files_analyzed"] == 1
    assert TestClient(app).post("/api/analyze", json={"path": "/etc"}).json()["repository"] == tmp_path.name


def test_missing_repo_returns_generic_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path / "not-here"))
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).post("/api/analyze")
    assert response.status_code == 503
    assert "not-here" not in response.text


def test_relative_config_is_relative_to_project_root_not_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    analyze_module = importlib.import_module("backend.api.analyze")
    sample = tmp_path / "sample_repo"
    sample.mkdir()
    (sample / "app.py").write_text("print('sample')\n", encoding="utf-8")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.setattr(analyze_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", "sample_repo")
    monkeypatch.chdir(unrelated)
    response = TestClient(FastAPI(routes=router.routes)).post("/api/analyze")
    assert response.status_code == 200
    assert response.json()["files_analyzed"] == 1
    assert response.json()["repository"] == "sample_repo"


def test_default_repo_is_relative_to_project_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    analyze_module = importlib.import_module("backend.api.analyze")
    sample = tmp_path / "sample_repo"
    sample.mkdir()
    (sample / "app.py").write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr(analyze_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("REPOMEDIC_SAMPLE_REPO", raising=False)
    monkeypatch.chdir(tmp_path)
    assert TestClient(FastAPI(routes=router.routes)).post("/api/analyze").status_code == 200


def test_architecture_inspection_keeps_analysis_contract_unchanged(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("pass\n", encoding="utf-8")
    structure = inspect_repository_structure(tmp_path)
    assert structure == {
        "repository": tmp_path.name,
        "top_level_directories": ["src"],
        "entry_points": ["src/main.py"],
    }
    assert set(analyze_repository(tmp_path)) == {
        "repository", "files_analyzed", "languages", "health_score", "findings",
    }


def test_controlled_demo_contains_expected_static_findings() -> None:
    project_root = Path(__file__).resolve().parents[1]
    sample = project_root / "sample_repo"
    result = analyze_repository(sample)
    assert result["files_analyzed"] == 3
    assert result["languages"] == ["JavaScript", "Python"]
    assert {f["category"] for f in result["findings"]} >= {
        "security", "testing", "error_handling", "documentation",
    }
    assert "FAKE_DEMO_KEY_NOT_REAL" not in json.dumps(result)
    structure = inspect_repository_structure(sample)
    assert structure["entry_points"] == ["app.py"]
    assert structure["top_level_directories"] == ["frontend"]


def test_member2_preview_has_exactly_one_analyze_route(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path))

    from backend.preview import app
    from backend.api.analyze import router as analyze_router

    paths = [
        route.path
        for route in analyze_router.routes
        if hasattr(route, "path")
    ]

    assert paths.count("/api/analyze") == 1

    response = TestClient(app).post("/api/analyze")
    assert response.status_code == 200, response.text
