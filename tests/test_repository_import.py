import io
import os
from pathlib import Path
import stat
import zipfile

import pytest

from backend.services import repository_import as imports
from backend.services.workspaces import RepositoryError
from tests.test_workspaces import workspace_registry


def archive_bytes(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, content in files:
            bundle.writestr(name, content)
    return output.getvalue()


@pytest.mark.parametrize("url", [
    "http://github.com/a/b", "https://evil.com/a/b", "git@github.com:a/b",
    "ssh://github.com/a/b", "https://user:secret@github.com/a/b",
    "https://github.com:443/a/b", "https://github.com.evil.com/a/b",
    "https://github.com/a/b/tree/main", "https://github.com/a/b?token=secret",
    "https://github.com/a/b#main", "https://github.com/a/%2e%2e",
    "https://github.com/a/b\\c", "https://github.com/a/..",
    "https://github.com/a/b\n", " https://github.com/a/b", "file:///etc",
    "https://github.com/a/b?", "https://github.com/a/b#",
])
def test_invalid_github_urls(url):
    with pytest.raises(RepositoryError) as error:
        imports.github_url(url)
    assert error.value.status == 422


def test_github_canonical_url():
    assert imports.github_url("https://GitHub.com/owner/project.git/") == "https://github.com/owner/project"


@pytest.mark.parametrize("name", [
    "../outside.py", "/tmp/outside.py", "C:/outside.py", "a\\..\\outside.py",
    "a/../../x.py", "a//x.py", "./x.py", "con.py", "a./x.py",
    ".git/config", ".GIT/config", "x/aux.txt", "a\x00b.py",
    "/".join(["a"] * 31),
])
def test_unsafe_member_paths(name):
    with pytest.raises(RepositoryError):
        imports.member_parts(name)


def test_zip_real_extraction_and_wrapper_directory(workspace_registry):
    data = archive_bytes([("wrapper/hello.py", "print('hello')"), ("wrapper/README.md", "hello")])
    item = imports.import_zip(workspace_registry, io.BytesIO(data), "../hello.zip")
    assert item.root.name == "wrapper"
    assert (item.root / "hello.py").read_text() == "print('hello')"
    assert item.display_name == "hello"
    assert not item.trusted_demo
    assert not list((workspace_registry.root / "staging").iterdir())


@pytest.mark.parametrize("files", [
    [("../escape.py", "x")], [(".git/config", "x")],
    [("a.py", "x"), ("A.py", "y")], [("a", "x"), ("a/b.py", "y")],
    [("a/x.py", "x"), ("A/y.py", "y")],
])
def test_bad_zip_never_publishes(workspace_registry, files):
    with pytest.raises(RepositoryError):
        imports.import_zip(workspace_registry, io.BytesIO(archive_bytes(files)), "bad.zip")
    assert not workspace_registry.records
    assert not list((workspace_registry.root / "staging").iterdir())


@pytest.mark.parametrize("mode", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR])
def test_zip_special_files_rejected(workspace_registry, mode):
    entry = zipfile.ZipInfo("link.py")
    entry.create_system = 3
    entry.external_attr = (mode | 0o777) << 16
    with pytest.raises(RepositoryError):
        imports.import_zip(workspace_registry, io.BytesIO(archive_bytes([(entry, "/etc/passwd")])), "bad.zip")


@pytest.mark.parametrize("setting,value", [("MAX_UPLOAD", 10), ("MAX_FILE", 3), ("MAX_EXTRACTED", 5), ("MAX_ENTRIES", 1)])
def test_zip_limits(workspace_registry, monkeypatch, setting, value):
    monkeypatch.setattr(imports, setting, value)
    data = archive_bytes([("a.py", "abcdef"), ("b.py", "ghijkl")])
    with pytest.raises(RepositoryError) as error:
        imports.import_zip(workspace_registry, io.BytesIO(data), "big.zip")
    assert error.value.status == 413
    assert not workspace_registry.records


def test_corrupt_archive_and_timeout(workspace_registry, monkeypatch):
    with pytest.raises(RepositoryError):
        imports.import_zip(workspace_registry, io.BytesIO(b"not a zip"), "x.zip")
    monkeypatch.setattr(imports, "ZIP_SECONDS", -1)
    with pytest.raises(RepositoryError) as error:
        imports.import_zip(workspace_registry, io.BytesIO(archive_bytes([("a.py", "pass")])), "x.zip")
    assert error.value.status == 504


def fake_git_transport(monkeypatch, files):
    """Mock transport only; real tree validation/materialization/registry execute."""
    calls = []
    oid_files = [(format(index, "040x").encode(), name, data) for index, (name, data) in enumerate(files, 1)]

    def run(executable, args, stage, env, deadline, limit, input_bytes=b""):
        calls.append(args)
        if args[0] == "clone":
            (Path(args[-1]) / ".git").mkdir(parents=True)
            return b""
        if "rev-parse" in args:
            return b"a" * 40 + b"\n"
        if "ls-tree" in args:
            return b"".join(b"100644 blob " + oid + b" " + str(len(data)).encode() + b"\t" + name.encode() + b"\0"
                            for oid, name, data in oid_files)
        assert "cat-file" in args
        assert input_bytes == b"".join(oid + b"\n" for oid, _, _ in oid_files)
        return b"".join(oid + b" blob " + str(len(data)).encode() + b"\n" + data + b"\n" for oid, _, data in oid_files)

    monkeypatch.setattr(imports.shutil, "which", lambda *a, **kw: "/usr/bin/git")
    monkeypatch.setattr(imports, "_run_git", run)
    return calls


def test_github_materializes_raw_objects(workspace_registry, monkeypatch):
    calls = fake_git_transport(monkeypatch, [("external.py", b"print('external')")])
    item = imports.import_github(workspace_registry, "https://github.com/example/external")
    assert (item.root / "external.py").read_bytes() == b"print('external')"
    assert item.source == "github" and item.details["commit_sha"] == "a" * 40
    assert "--no-checkout" in calls[0] and "--depth=1" in calls[0]
    assert not (item.owned / "objects").exists()
    assert not item.trusted_demo


def test_git_environment_drops_credentials_and_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("HTTPS_PROXY", "http://evil")
    env = imports._git_environment(tmp_path)
    assert "GITHUB_TOKEN" not in env and "GIT_CONFIG_COUNT" not in env and "HTTPS_PROXY" not in env
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_ALLOW_PROTOCOL"] == "https"
    assert env["HOME"] == str(tmp_path / "environment")


@pytest.mark.parametrize("scenario,status", [("timeout", 504), ("oversize", 413), ("failure", 404)])
def test_git_subprocess_failure_cleanup(tmp_path, monkeypatch, scenario, status):
    captured = {}
    killed = []

    class FakeProcess:
        pid = 123456789
        returncode = 1 if scenario == "failure" else None

        def poll(self):
            return self.returncode

        def wait(self):
            captured["waited"] = True

    def popen(command, **kwargs):
        captured.update(kwargs)
        captured["command"] = command
        if scenario == "oversize":
            kwargs["stdout"].write(b"too large")
            kwargs["stdout"].flush()
        return FakeProcess()

    monkeypatch.setattr(imports.subprocess, "Popen", popen)
    monkeypatch.setattr(imports.os, "killpg", lambda pid, sig: killed.append(pid))
    deadline = imports.time.monotonic() + (-1 if scenario == "timeout" else 60)
    with pytest.raises(RepositoryError) as error:
        imports._run_git("git", ["clone", "--", "https://github.com/a/b.git"], tmp_path,
                         {}, deadline, 3)
    assert error.value.status == status
    assert captured["shell"] is False and captured["start_new_session"] is True
    assert "http.followRedirects=false" in captured["command"]
    assert "credential.helper=" in captured["command"]
    assert captured["waited"] and killed
    assert list(tmp_path.iterdir()) == []
