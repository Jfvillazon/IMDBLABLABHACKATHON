import os

from fastapi.testclient import TestClient
import pytest

from backend.main import app
from backend.services import repository_import as imports
from tests.test_repository_import import archive_bytes, fake_git_transport
from tests.test_workspaces import workspace_registry


@pytest.fixture
def repository_client(workspace_registry, monkeypatch):
    monkeypatch.setattr(app.state, "repositories", workspace_registry, raising=False)
    with TestClient(app) as client:
        yield client


def upload(client, name, files):
    response = client.post("/api/repositories/zip", files={"file": (name, archive_bytes(files), "application/zip")})
    assert response.status_code == 201, response.text
    return response.json()


def analysis(client, identifier):
    response = client.post("/api/repositories/{}/analyze".format(identifier))
    assert response.status_code == 200, response.text
    assert response.json()["repository_id"] == identifier
    return response.json()["analysis"]


def test_two_real_zip_workspaces_and_demo_never_cross_resolve(repository_client, workspace_registry):
    first = upload(repository_client, "alpha.zip", [("alpha_unique.py", 'API_KEY = "fake_alpha_test_key"\n')])
    second = upload(repository_client, "bravo.zip", [("bravo_unique.py", 'API_KEY = "fake_bravo_test_key"\n')])
    demo = repository_client.post("/api/repositories/demo").json()
    assert len({first["repository_id"], second["repository_id"], demo["repository_id"]}) == 3
    baseline = analysis(repository_client, demo["repository_id"])
    for descriptor, expected, other in [(first, "alpha_unique.py", "bravo_unique.py"),
                                        (second, "bravo_unique.py", "alpha_unique.py"),
                                        (first, "alpha_unique.py", "bravo_unique.py")]:
        result = analysis(repository_client, descriptor["repository_id"])
        paths = {item["file"] for item in result["findings"]}
        assert expected in paths and other not in paths
        assert "checkout.py" not in paths and "app.py" not in paths
        assert result["files_analyzed"] == 1
        assert result["repository"] == descriptor["display_name"]
        assert str(workspace_registry.root) not in str(result)
        assert descriptor["source"] == "zip"
        assert descriptor["capabilities"] == {"analyze": True, "investigate": True, "validate": False}
    assert analysis(repository_client, demo["repository_id"]) == baseline


def test_github_and_zip_use_independent_ingestion_paths(repository_client, monkeypatch):
    calls = fake_git_transport(monkeypatch, [("github_unique.py", b'API_KEY = "fake_remote_test_key"\n')])
    response = repository_client.post("/api/repositories/github", json={"url": "https://github.com/member1/external"})
    assert response.status_code == 201, response.text
    github = response.json()
    zipped = upload(repository_client, "upload.zip", [("zip_unique.py", 'API_KEY = "fake_zip_test_key"\n')])
    assert calls[0][0] == "clone"
    assert github["source"] == "github" and zipped["source"] == "zip"
    assert github["repository_id"] != zipped["repository_id"]
    for descriptor, expected, other in [(github, "github_unique.py", "zip_unique.py"),
                                        (zipped, "zip_unique.py", "github_unique.py")]:
        result = analysis(repository_client, descriptor["repository_id"])
        paths = {finding["file"] for finding in result["findings"]}
        assert expected in paths and other not in paths and "checkout.py" not in paths


def test_same_project_imported_twice_has_independent_ids(repository_client, monkeypatch):
    content = b'API_KEY = "fake_shared_test_key"\n'
    fake_git_transport(monkeypatch, [("same.py", content)])
    remote = repository_client.post("/api/repositories/github", json={"url": "https://github.com/member1/same"}).json()
    zipped = upload(repository_client, "same.zip", [("same.py", content)])
    assert remote["repository_id"] != zipped["repository_id"]
    assert analysis(repository_client, remote["repository_id"]) == analysis(repository_client, zipped["repository_id"])
    assert repository_client.delete("/api/repositories/" + remote["repository_id"]).status_code == 204
    assert repository_client.post("/api/repositories/" + remote["repository_id"] + "/analyze").status_code == 404
    assert analysis(repository_client, zipped["repository_id"])["files_analyzed"] == 1


@pytest.mark.parametrize("operation", ["analyze", "investigate", "validate", "workflow"])
def test_unknown_id_never_falls_back_to_demo(repository_client, operation):
    body = {"issue": "checkout"} if operation in {"investigate", "workflow"} else None
    response = repository_client.post("/api/repositories/unknown/" + operation, json=body)
    assert response.status_code == 404


def test_client_paths_and_execution_flags_are_rejected(repository_client):
    assert repository_client.post("/api/repositories/demo", json={"path": "/etc"}).status_code == 422
    assert repository_client.post("/api/repositories/github", json={"url": "https://github.com/a/b", "path": "/etc"}).status_code == 422
    demo = repository_client.post("/api/repositories/demo").json()["repository_id"]
    assert repository_client.post("/api/repositories/" + demo + "/analyze", json={"path": "/etc"}).status_code == 422
    assert repository_client.post("/api/repositories/" + demo + "/workflow", json={"issue": "x", "execute": True}).status_code == 422


def test_descriptor_get_delete_and_missing_id(repository_client):
    item = upload(repository_client, "hello.zip", [("hello.py", "pass")])
    url = "/api/repositories/" + item["repository_id"]
    assert repository_client.get(url).json()["display_name"] == "hello"
    assert repository_client.delete(url).status_code == 204
    assert repository_client.get(url).status_code == 404
    assert repository_client.delete(url).status_code == 404


@pytest.mark.parametrize("parts", [
    [("wrong", ("a.zip", b"x"))],
    [("file", ("a.zip", b"x")), ("file", ("b.zip", b"y"))],
    [("file", ("a.zip", b"x")), ("path", (None, "/etc"))],
])
def test_multipart_contract_rejects_extra_or_wrong_parts(repository_client, parts):
    assert repository_client.post("/api/repositories/zip", files=parts).status_code == 422


def test_bad_upload_does_not_expose_workspace_or_publish(repository_client, workspace_registry):
    response = repository_client.post("/api/repositories/zip", files={"file": ("bad.zip", b"invalid")})
    assert response.status_code == 422
    assert str(workspace_registry.root) not in response.text
    assert not workspace_registry.records
    assert not list((workspace_registry.root / "staging").iterdir())


def test_body_limit_applies_before_parsing_even_without_content_length(repository_client, monkeypatch):
    monkeypatch.setattr("backend.api.repositories.MAX_UPLOAD", 10)
    response = repository_client.post("/api/repositories/zip", content=iter([b"x" * 600000, b"y" * 600000]),
                                      headers={"content-type": "multipart/form-data; boundary=x"})
    assert response.status_code == 413


def test_json_body_limit_and_content_length_rejection(repository_client):
    assert repository_client.post("/api/repositories/github", content=b"x" * 17000).status_code == 413
    assert repository_client.post("/api/repositories/zip", headers={"content-length": "999999999"}).status_code == 413


def test_scoped_demo_ignores_legacy_environment_overrides(repository_client, monkeypatch, tmp_path):
    monkeypatch.setenv("REPOMEDIC_SAMPLE_REPO", str(tmp_path))
    monkeypatch.setenv("REPO_MEDIC_REPO_PATH", str(tmp_path))
    descriptor = repository_client.post("/api/repositories/demo").json()
    assert descriptor["display_name"] == "sample_repo"
    assert analysis(repository_client, descriptor["repository_id"])["files_analyzed"] > 0


@pytest.mark.skipif(os.environ.get("REPOMEDIC_RUN_LIVE_GITHUB") != "1",
                    reason="Opt-in live Git clone disabled; requires explicit Git/network authorization")
def test_live_public_github_import(repository_client):
    """Member 1 supplies a public fixture with a known finding-bearing filename."""
    url = os.environ["REPOMEDIC_LIVE_GITHUB_URL"]
    expected = os.environ["REPOMEDIC_LIVE_GITHUB_FINDING_FILE"]
    response = repository_client.post("/api/repositories/github", json={"url": url})
    assert response.status_code == 201, response.text
    descriptor = response.json()
    assert descriptor["source"] == "github"
    assert len(descriptor["source_details"]["commit_sha"]) in {40, 64}
    result = analysis(repository_client, descriptor["repository_id"])
    assert expected in {finding["file"] for finding in result["findings"]}
