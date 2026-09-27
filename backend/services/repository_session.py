"""Shared active-repository state for the RepoMedic hackathon prototype."""

from __future__ import annotations

from pathlib import Path
from threading import Lock


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEMO_REPOSITORY = (_PROJECT_ROOT / "sample_repo").resolve()

_active_repository: Path = _DEMO_REPOSITORY
_lock = Lock()


def set_active_repository(repo_path: str | Path) -> Path:
    """Set the repository used by Analyze, Investigate, and Validate."""
    path = Path(repo_path).expanduser()

    if not path.is_dir():
        raise ValueError("Repository directory does not exist or is not accessible.")

    path = path.resolve(strict=True)

    if path.is_symlink():
        raise ValueError("Symbolic-link repository roots are not allowed.")

    with _lock:
        global _active_repository
        _active_repository = path

    return path


def get_active_repository() -> Path:
    """Return the repository currently selected for this server instance."""
    with _lock:
        return _active_repository


def use_demo_repository() -> Path:
    """Switch RepoMedic back to the bundled demonstration repository."""
    return set_active_repository(_DEMO_REPOSITORY)