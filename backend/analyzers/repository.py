from pathlib import Path
from collections import Counter


IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".pytest_cache"
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".html": "HTML",
    ".css": "CSS"
}


def scan_repository(repo_path: str):
    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(f"Repository does not exist: {repo_path}")

    files = []
    language_counts = Counter()

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue

        files.append(path)

        language = LANGUAGE_MAP.get(path.suffix.lower())

        if language:
            language_counts[language] += 1

    return {
        "repository": root.name,
        "files": files,
        "files_analyzed": len(files),
        "languages": list(language_counts.keys())
    }