"""
Validation Engine — RepoMedic.

Public interface:
    run_validation(test_path: str) -> ValidateResponse

Algorithm:
  1. Validate that the target test path exists and is accessible.
  2. Invoke pytest via subprocess with a fixed, safe argument list.
  3. Parse pytest's exit code and JSON result summary to produce counts.
  4. Return a ValidateResponse with accurate tests_run / passed / failed / status.

Security:
  - subprocess is never called with shell=True.
  - Only a pre-approved fixed argument list is used — no user-supplied commands.
  - The test_path argument controls which directory is tested, but it is
    resolved and validated server-side, not taken verbatim from the HTTP body.

Test-count strategy:
  - We use pytest --tb=no -q which emits a summary line such as:
        "3 passed, 1 failed in 0.12s"
        "5 passed in 0.07s"
        "1 failed in 0.08s"
        "no tests ran"
  - We parse that terminal summary line with a regex.
  - If parsing fails (no recognisable summary), we fall back to status="error".
  - We do NOT fabricate counts.

Exit-code semantics (pytest):
  0  — all collected tests passed
  1  — tests were collected and one or more failed
  2  — test execution was interrupted
  3  — internal error
  4  — command-line usage error (bad arguments)
  5  — no tests were collected
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from backend.models.schemas import ValidateResponse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum time (seconds) to wait for pytest to complete before aborting.
_SUBPROCESS_TIMEOUT = 60

# Regex to independently extract passed and failed counts from a line.
# pytest summary lines can appear in either order:
#   "3 passed, 1 failed in 0.12s"
#   "1 failed, 1 passed in 0.00s"  ← failed before passed
#   "5 passed in 0.07s"
#   "2 failed in 0.05s"
#   "no tests ran"
_PASSED_RE = re.compile(r"(\d+)\s+passed", re.IGNORECASE)
_FAILED_RE = re.compile(r"(\d+)\s+failed", re.IGNORECASE)

_NO_TESTS_RE = re.compile(r"no tests ran", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_counts(output: str) -> tuple[int, int] | None:
    """
    Extract (passed, failed) counts from pytest terminal output.

    Scans the output lines from the bottom up for the first line that
    contains test-result words so we find the summary rather than a
    coincidental match in a test name.

    Returns (passed, failed) or None if unparseable.

    Note: pytest orders the summary tokens inconsistently across versions
    (e.g. "1 failed, 1 passed" vs "1 passed, 1 failed"), so each count is
    extracted independently.
    """
    lines = output.splitlines()
    # Scan from the bottom because the summary is the last significant line.
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue

        # Handle "no tests ran"
        if _NO_TESTS_RE.search(line):
            return (0, 0)

        # Only examine lines that look like a result summary.
        if "passed" not in line.lower() and "failed" not in line.lower():
            continue

        m_passed = _PASSED_RE.search(line)
        m_failed = _FAILED_RE.search(line)

        if m_passed or m_failed:
            passed = int(m_passed.group(1)) if m_passed else 0
            failed = int(m_failed.group(1)) if m_failed else 0
            return (passed, failed)

    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def run_validation(test_path: str) -> ValidateResponse:
    """
    Execute pytest against *test_path* and return a structured ValidateResponse.

    Parameters
    ----------
    test_path:
        Filesystem path to the directory (or file) containing tests to run.
        Must exist and be a directory or file — validated before subprocess
        is invoked.

    Returns
    -------
    ValidateResponse
        Always returns a response; never raises for normal pytest outcomes.
        Returns status="error" for infrastructure problems.
    """
    # ------------------------------------------------------------------
    # Path validation — never pass an unvalidated path to subprocess.
    # ------------------------------------------------------------------
    target = Path(test_path)
    if not target.exists():
        return ValidateResponse(
            tests_run=0,
            passed=0,
            failed=0,
            status="error",
        )
    if not (target.is_dir() or target.is_file()):
        return ValidateResponse(
            tests_run=0,
            passed=0,
            failed=0,
            status="error",
        )

    # ------------------------------------------------------------------
    # Build a fixed, safe argument list — no shell=True, no user commands.
    # ------------------------------------------------------------------
    cmd = [
        sys.executable,   # the same Python interpreter running the server
        "-m", "pytest",
        str(target),
        "--tb=no",        # suppress tracebacks for brevity
        "-q",             # quiet summary output only
    ]

    # ------------------------------------------------------------------
    # Execute with a hard timeout.
    # ------------------------------------------------------------------
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return ValidateResponse(
            tests_run=0,
            passed=0,
            failed=0,
            status="error",
        )
    except OSError:
        # e.g. Python interpreter not found — should never happen in practice.
        return ValidateResponse(
            tests_run=0,
            passed=0,
            failed=0,
            status="error",
        )

    # ------------------------------------------------------------------
    # Interpret exit code.
    # Exit code 5 = no tests collected.
    # ------------------------------------------------------------------
    if result.returncode == 5:
        return ValidateResponse(
            tests_run=0,
            passed=0,
            failed=0,
            status="error",
        )

    # Combine stdout + stderr for parsing (pytest may write to either).
    combined = (result.stdout or "") + "\n" + (result.stderr or "")

    counts = _parse_counts(combined)
    if counts is None:
        # Output not parseable — safe fallback.
        return ValidateResponse(
            tests_run=0,
            passed=0,
            failed=0,
            status="error",
        )

    passed, failed = counts
    tests_run = passed + failed

    if result.returncode == 0:
        status: str = "passed"
    elif result.returncode == 1:
        status = "failed"
    else:
        # Exit codes 2, 3, 4 indicate execution problems.
        status = "error"

    return ValidateResponse(
        tests_run=tests_run,
        passed=passed,
        failed=failed,
        status=status,
    )
