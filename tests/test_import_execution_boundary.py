from pathlib import Path

import pytest

from backend.services.investigation import investigate_issue
from tests.test_repository_api import repository_client, upload, analysis
from tests.test_workspaces import workspace_registry
from tests.test_repository_import import fake_git_transport


@pytest.mark.parametrize("source", ["zip", "github"])
def test_imported_code_never_executes_through_any_scoped_flow(repository_client, monkeypatch, tmp_path, source):
    marker = tmp_path / "executed"
    hostile = "from pathlib import Path\nPath({!r}).write_text('executed')\n".format(str(marker))
    files = [("conftest.py", hostile), ("test_evil.py", hostile), ("setup.py", hostile),
             ("evil.py", hostile), ("pytest.ini", "[pytest]\naddopts = --bad-option\n")]

    def forbidden(*args, **kwargs):
        pytest.fail("Imported repository attempted subprocess/code execution")

    monkeypatch.setattr("subprocess.run", forbidden)
    monkeypatch.setattr("subprocess.Popen", forbidden)
    if source == "zip":
        descriptor = upload(repository_client, "hostile.zip", files)
    else:
        fake_git_transport(monkeypatch, [(name, content.encode()) for name, content in files])
        response = repository_client.post("/api/repositories/github", json={"url": "https://github.com/member1/hostile"})
        assert response.status_code == 201
        descriptor = response.json()
    identifier = descriptor["repository_id"]
    assert not descriptor["capabilities"]["validate"]
    assert analysis(repository_client, identifier)["files_analyzed"] == 4
    base = "/api/repositories/" + identifier
    investigation = repository_client.post(base + "/investigate", json={"issue": "evil checkout"})
    assert investigation.status_code == 200
    validation = repository_client.post(base + "/validate").json()["validation"]
    assert validation == {"tests_run": 0, "passed": 0, "failed": 0,
                          "status": "not_run", "reason": "untrusted_repository"}
    report = repository_client.post(base + "/workflow", json={"issue": "evil checkout"}).json()["report"]
    assert report["validation_status"] == "not_run"
    assert report["validation_reason"] == "untrusted_repository"
    assert report["tests_run"] == 0 and "not run" in report["outcome"]
    assert not marker.exists()


def test_investigation_skips_symlinks_and_large_files(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    external = tmp_path / "outside.py"
    external.write_text("checkout quantity " * 10)
    (project / "checkout_link.py").symlink_to(external)
    (project / "checkout_large.py").write_text("checkout quantity " * 40000)
    (project / "checkout_safe.py").write_text("def checkout(quantity): return quantity * 10")
    result = investigate_issue("checkout quantity missing", str(project))
    assert result.relevant_files == ["checkout_safe.py"]


def test_scoped_demo_validation_uses_only_trusted_fixture(repository_client, monkeypatch):
    from backend.models.schemas import ValidateResponse
    from backend.services.workspaces import DEMO_ROOT
    calls = []

    def validation(path):
        calls.append(path)
        return ValidateResponse(tests_run=1, passed=1, failed=0, status="passed")

    monkeypatch.setattr("backend.services.repository_operations.run_validation", validation)
    identifier = repository_client.post("/api/repositories/demo").json()["repository_id"]
    result = repository_client.post("/api/repositories/" + identifier + "/validate").json()
    assert result["validation"]["status"] == "passed"
    assert calls == [str(DEMO_ROOT)]
