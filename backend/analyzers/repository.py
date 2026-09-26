"""Bounded, deterministic discovery of source files without following symlinks."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

# Never traverse dependency trees, generated artifacts, credential directories,
# or version-control metadata. Directories that start with '.' are also skipped.
IGNORED_DIRECTORIES = frozenset({
    ".git", ".hg", ".svn", ".idea", ".vscode", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".next", ".nuxt", ".tox",
    "__pycache__", "node_modules", "venv", ".venv", "env", ".env",
    "dist", "build", "coverage", ".coverage", "target", "vendor",
    "bower_components", "site-packages", "bob_sessions",
})

LANGUAGE_BY_SUFFIX = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java", ".go": "Go", ".rs": "Rust",
    ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".sh": "Shell", ".sql": "SQL",
}
MAX_FILES = 3_000
MAX_FILE_BYTES = 512 * 1024


class RepositoryScan(TypedDict):
    repository: str
    root: Path
    files: list[Path]
    files_analyzed: int
    languages: list[str]


def scan_repository(repo_path: str | Path) -> RepositoryScan:
    """Discover a bounded set of regular source files under an operator-chosen root.

    No symbolic links are followed; directory walk is sorted for repeatability.
    Never pass an untrusted HTTP-supplied path to this function.
    """
    root = Path(repo_path).expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Repository directory is missing or invalid")
    root = root.resolve(strict=True)

    files: list[Path] = []
    languages: set[str] = set()

    def walk_error(_error: OSError) -> None:
        # Inaccessible directories are ignored rather than aborting the run.
        return None

    for current, dirs, names in os.walk(root, topdown=True,
                                        followlinks=False, onerror=walk_error):
        directory = Path(current)
        dirs[:] = sorted(
            name for name in dirs
            if name not in IGNORED_DIRECTORIES
            and not name.startswith(".")
            and not (directory / name).is_symlink()
        )
        for name in sorted(names):
            path = directory / name
            # Hidden and secret-bearing configuration files are never read.
            if name.startswith(".") or path.is_symlink():
                continue
            language = LANGUAGE_BY_SUFFIX.get(path.suffix.lower())
            if language is None:
                continue
            try:
                if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            files.append(path)
            languages.add(language)
            if len(files) >= MAX_FILES:
                break
        if len(files) >= MAX_FILES:
            break

    files.sort(key=lambda path: path.relative_to(root).as_posix())
    return {
        "repository": root.name,
        "root": root,
        "files": files,
        "files_analyzed": len(files),
        "languages": sorted(languages),
    }
