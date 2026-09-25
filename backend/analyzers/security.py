import re
from pathlib import Path


SECRET_PATTERN = re.compile(
    r"""(?i)
    (api[_-]?key|secret|password|token)
    \s*=\s*
    ["'][^"']+["']
    """,
    re.VERBOSE
)


def analyze_security(files, root: Path):
    findings = []

    for file_path in files:
        if file_path.suffix != ".py":
            continue

        try:
            lines = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).splitlines()
        except OSError:
            continue

        for line_number, line in enumerate(lines, start=1):

            if SECRET_PATTERN.search(line):

                findings.append({
                    "category": "security",
                    "severity": "high",
                    "title": "Potential hardcoded secret",
                    "file": str(file_path.relative_to(root)),
                    "line": line_number,
                    "description":
                        "A possible credential is stored directly in source code.",
                    "recommendation":
                        "Move credentials to environment configuration."
                })

    return findings