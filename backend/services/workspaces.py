"""Process-local repository registry with leases and private owned storage.

V1 runs one application worker on POSIX. IDs are capabilities, not authentication.
Only this module grants demo execution permission; imports cannot request it.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import fcntl
import os
from pathlib import Path
import secrets
import shutil
import tempfile
import threading
import time
from typing import Dict, Iterator, Optional

from backend.models.repositories import Capabilities, RepositoryDescriptor

DEMO_ROOT = Path(__file__).resolve().parents[2] / "sample_repo"
IDLE_TTL = 3600
MAX_TTL = 14400
MAX_WORKSPACES = 8
MAX_IMPORTS = 2


class RepositoryError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


@dataclass
class RepositoryWorkspace:
    repository_id: str
    source: str
    display_name: str
    root: Path
    owned: Optional[Path]
    created: float
    accessed: float
    details: Dict[str, str] = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    leases: int = 0

    @property
    def trusted_demo(self) -> bool:
        return self.source == "demo" and self.owned is None and self.root == DEMO_ROOT

    @property
    def expiry(self) -> float:
        return min(self.created + MAX_TTL, self.accessed + IDLE_TTL)

    def descriptor(self) -> RepositoryDescriptor:
        return RepositoryDescriptor(
            repository_id=self.repository_id, source=self.source,
            display_name=self.display_name,
            created_at=datetime.fromtimestamp(self.created, timezone.utc),
            expires_at=datetime.fromtimestamp(self.expiry, timezone.utc),
            capabilities=Capabilities(validate=self.trusted_demo),
            source_details=self.details, warnings=self.warnings,
        )


class WorkspaceRegistry:
    def __init__(self, parent: Optional[Path] = None, clock=time.time):
        self.clock = clock
        self.lock = threading.RLock()
        self.records: Dict[str, RepositoryWorkspace] = {}
        self.imports = 0
        self.closed = False
        parent = parent or Path(os.environ.get(
            "REPOMEDIC_WORKSPACE_ROOT",
            str(Path(tempfile.gettempdir()) / ("repomedic-workspaces-" + str(os.getuid()))),
        ))
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = parent.lstat()
        if parent.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise RepositoryError(503, "Workspace storage must be private and operator-owned")
        self.parent = parent.resolve()
        self._reap_stale_instances()
        self.root = Path(tempfile.mkdtemp(prefix="instance-", dir=str(self.parent)))
        self.guard = (self.root / ".lock").open("w")
        fcntl.flock(self.guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (self.root / "staging").mkdir(mode=0o700)
        (self.root / "ready").mkdir(mode=0o700)

    def _reap_stale_instances(self):
        for path in self.parent.glob("instance-*"):
            if path.is_symlink() or not path.is_dir():
                continue
            if path.stat().st_uid != os.getuid() or time.time() - path.stat().st_mtime < MAX_TTL:
                continue
            guard = path / ".lock"
            if guard.is_symlink() or not guard.is_file():
                continue
            with guard.open("r") as handle:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                shutil.rmtree(path)

    def _capacity(self):
        if self.closed or len(self.records) + self.imports >= MAX_WORKSPACES:
            raise RepositoryError(503, "Repository workspace capacity reached")

    def demo(self) -> RepositoryWorkspace:
        with self.lock:
            self.cleanup()
            self._capacity()
            if DEMO_ROOT.is_symlink() or not DEMO_ROOT.is_dir():
                raise RepositoryError(503, "Built-in demo unavailable")
            now = self.clock()
            item = RepositoryWorkspace(secrets.token_urlsafe(24), "demo", "sample_repo",
                                       DEMO_ROOT, None, now, now)
            self.records[item.repository_id] = item
            return item

    @contextmanager
    def staging(self) -> Iterator[Path]:
        with self.lock:
            self.cleanup()
            self._capacity()
            if self.imports >= MAX_IMPORTS:
                raise RepositoryError(503, "Repository import capacity reached")
            self.imports += 1
            try:
                path = Path(tempfile.mkdtemp(prefix="import-", dir=str(self.root / "staging")))
            except BaseException:
                self.imports -= 1
                raise
        try:
            yield path
        finally:
            with self.lock:
                if path.exists():
                    self._remove_owned(path)
                self.imports -= 1

    def publish(self, stage: Path, repository: Path, source: str, name: str,
                details=None, warnings=None) -> RepositoryWorkspace:
        with self.lock:
            if self.closed or source not in {"github", "zip"}:
                raise RepositoryError(503, "Repository import unavailable")
            if stage.parent != self.root / "staging" or stage.is_symlink():
                raise RepositoryError(503, "Invalid workspace")
            relative = repository.resolve().relative_to(stage.resolve())
            if repository.is_symlink() or not repository.is_dir():
                raise RepositoryError(422, "Invalid repository")
            identifier = secrets.token_urlsafe(24)
            destination = self.root / "ready" / identifier
            stage.rename(destination)
            now = self.clock()
            item = RepositoryWorkspace(identifier, source, name, destination / relative,
                                       destination, now, now, details or {}, warnings or [])
            self.records[identifier] = item
            return item

    @contextmanager
    def lease(self, identifier: str) -> Iterator[RepositoryWorkspace]:
        with self.lock:
            self.cleanup()
            item = self.records.get(identifier)
            if item is None or item.expiry <= self.clock():
                raise RepositoryError(404, "Repository unavailable or expired")
            if item.root.is_symlink() or not item.root.is_dir():
                raise RepositoryError(404, "Repository unavailable or expired")
            item.leases += 1
            item.accessed = self.clock()
        try:
            yield item
        finally:
            with self.lock:
                item.leases -= 1

    def _remove_owned(self, path: Path):
        if path.parent not in {self.root / "ready", self.root / "staging"} or path.is_symlink():
            raise RepositoryError(503, "Invalid workspace cleanup target")
        shutil.rmtree(path)

    def delete(self, identifier: str):
        with self.lock:
            item = self.records.get(identifier)
            if item is None:
                raise RepositoryError(404, "Repository unavailable or expired")
            if item.leases:
                raise RepositoryError(409, "Repository is busy")
            if item.owned is not None:
                self._remove_owned(item.owned)
            del self.records[identifier]

    def cleanup(self):
        with self.lock:
            for identifier, item in list(self.records.items()):
                if not item.leases and item.expiry <= self.clock():
                    self.delete(identifier)

    def close(self):
        with self.lock:
            if self.imports or any(item.leases for item in self.records.values()):
                raise RepositoryError(409, "Repository operations are still active")
            if self.closed:
                return
            for identifier in list(self.records):
                self.delete(identifier)
            self.closed = True
            shutil.rmtree(self.root)
            self.guard.close()
