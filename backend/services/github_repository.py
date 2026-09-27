"""Controlled GitHub repository cloning for RepoMedic."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


GITHUB_HOST = "github.com"
CLONE_TIMEOUT_SECONDS = 90

_REPOSITORY_PATH_PATTERN = re.compile(
    r"^/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$"
)


class GitHubRepositoryError(ValueError):
    """Raised when a GitHub repository cannot be safely prepared."""


def validate_github_url(repository_url: str) -> str:
    """Validate and normalize a public GitHub repository URL."""
    value = repository_url.strip()

    if not value:
        raise GitHubRepositoryError("GitHub repository URL is required.")

    parsed = urlparse(value)

    if parsed.scheme != "https":
        raise GitHubRepositoryError(
            "Only HTTPS GitHub repository URLs are supported."
        )

    if parsed.hostname is None or parsed.hostname.lower() != GITHUB_HOST:
        raise GitHubRepositoryError(
            "Only github.com repository URLs are supported."
        )

    if parsed.username or parsed.password:
        raise GitHubRepositoryError(
            "GitHub URLs containing credentials are not allowed."
        )

    try:
        port = parsed.port
    except ValueError as exc:
        raise GitHubRepositoryError(
            "Invalid GitHub repository URL."
        ) from exc

    if port is not None:
        raise GitHubRepositoryError(
            "Custom ports are not allowed in GitHub repository URLs."
        )

    if parsed.query or parsed.fragment:
        raise GitHubRepositoryError(
            "GitHub repository URL must not contain query parameters or fragments."
        )

    if not _REPOSITORY_PATH_PATTERN.fullmatch(parsed.path):
        raise GitHubRepositoryError(
            "Enter a GitHub repository URL in the form "
            "https://github.com/owner/repository"
        )

    normalized_path = parsed.path.rstrip("/")

    if normalized_path.endswith(".git"):
        normalized_path = normalized_path[:-4]

    return f"https://github.com{normalized_path}.git"


def clone_github_repository(repository_url: str) -> Path:
    """
    Clone a public GitHub repository into a controlled temporary directory.
    Uses a shallow clone to reduce download time and disk usage.
    """
    normalized_url = validate_github_url(repository_url)

    workspace = Path(
        tempfile.mkdtemp(prefix="repomedic-github-")
    ).resolve()

    repository_name = normalized_url.removesuffix(".git").rsplit("/", 1)[-1]
    repository_path = workspace / repository_name

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--",
        normalized_url,
        str(repository_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
            check=False,
            shell=False,
        )
    except FileNotFoundError as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise GitHubRepositoryError(
            "Git is not installed or is not available to RepoMedic."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise GitHubRepositoryError(
            "GitHub repository cloning timed out."
        ) from exc
    except OSError as exc:
        shutil.rmtree(workspace, ignore_errors=True)
        raise GitHubRepositoryError(
            "The GitHub repository could not be downloaded."
        ) from exc

    if result.returncode != 0:
        shutil.rmtree(workspace, ignore_errors=True)
        raise GitHubRepositoryError(
            "Unable to clone the GitHub repository. "
            "Make sure it exists and is publicly accessible."
        )

    if not repository_path.is_dir():
        shutil.rmtree(workspace, ignore_errors=True)
        raise GitHubRepositoryError(
            "GitHub repository clone did not produce a valid directory."
        )

    return repository_path