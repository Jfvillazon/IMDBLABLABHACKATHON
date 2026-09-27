from pathlib import Path
import os
import time

import pytest

from backend.services.workspaces import MAX_TTL, RepositoryError, WorkspaceRegistry


@pytest.fixture
def workspace_registry(tmp_path):
    registry = WorkspaceRegistry(tmp_path / "private")
    yield registry
    registry.close()


def register(registry, name="project"):
    with registry.staging() as stage:
        root = stage / "project"
        root.mkdir()
        (root / "unique.py").write_text("pass\n")
        return registry.publish(stage, root, "zip", name)


def test_ids_are_distinct_and_roots_are_private(workspace_registry):
    first = register(workspace_registry)
    second = register(workspace_registry)
    assert first.repository_id != second.repository_id
    assert first.root != second.root
    assert not first.trusted_demo
    assert str(workspace_registry.root) not in first.descriptor().model_dump_json()
    assert workspace_registry.root.stat().st_mode & 0o077 == 0


def test_demo_release_never_deletes_fixture(workspace_registry):
    demo = workspace_registry.demo()
    assert demo.trusted_demo and demo.descriptor().capabilities.can_validate
    workspace_registry.delete(demo.repository_id)
    assert demo.root.is_dir()


def test_leases_block_deletion_and_expiry_cleanup(workspace_registry):
    item = register(workspace_registry)
    now = [item.created]
    workspace_registry.clock = lambda: now[0]
    with workspace_registry.lease(item.repository_id):
        now[0] += MAX_TTL + 1
        workspace_registry.cleanup()
        assert item.root.exists()
        with pytest.raises(RepositoryError) as error:
            workspace_registry.delete(item.repository_id)
        assert error.value.status == 409
        with pytest.raises(RepositoryError):
            with workspace_registry.lease(item.repository_id):
                pass
    workspace_registry.cleanup()
    assert not item.root.exists()
    with pytest.raises(RepositoryError) as error:
        with workspace_registry.lease(item.repository_id):
            pass
    assert error.value.status == 404


def test_failed_import_cleans_staging(workspace_registry):
    with pytest.raises(ValueError):
        with workspace_registry.staging() as stage:
            (stage / "partial").write_text("partial")
            raise ValueError("interrupted")
    assert not stage.exists()
    assert workspace_registry.imports == 0


def test_import_capacity_and_trust_cannot_be_promoted(workspace_registry):
    with workspace_registry.staging() as first, workspace_registry.staging():
        with pytest.raises(RepositoryError) as error:
            with workspace_registry.staging():
                pass
        assert error.value.status == 503
        with pytest.raises(RepositoryError):
            workspace_registry.publish(first, first, "demo", "fake")


def test_foreign_and_symlink_cleanup_rejected(workspace_registry, tmp_path):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    with pytest.raises(RepositoryError):
        workspace_registry._remove_owned(foreign)
    link = workspace_registry.root / "ready" / "link"
    link.symlink_to(foreign)
    with pytest.raises(RepositoryError):
        workspace_registry._remove_owned(link)
    assert foreign.exists()


def test_stale_instances_reaped_but_active_instances_preserved(tmp_path):
    parent = tmp_path / "private"
    active = WorkspaceRegistry(parent)
    stale = parent / "instance-stale"
    stale.mkdir()
    (stale / ".lock").touch()
    old = time.time() - MAX_TTL - 10
    os.utime(stale, (old, old))
    os.utime(active.root, (old, old))
    second = WorkspaceRegistry(parent)
    try:
        assert not stale.exists()
        assert active.root.exists()
    finally:
        active.close()
        second.close()


def test_insecure_workspace_parent_rejected(tmp_path):
    parent = tmp_path / "public"
    parent.mkdir(mode=0o755)
    with pytest.raises(RepositoryError):
        WorkspaceRegistry(parent)
