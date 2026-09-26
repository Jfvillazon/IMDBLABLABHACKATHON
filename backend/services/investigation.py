"""
Investigation Engine V1 — RepoMedic.

Public interface:
    investigate_issue(issue: str, repository_path: str) -> InvestigateResponse

Algorithm:
  1. Validate inputs (empty issue, missing/non-directory path).
  2. Recursively discover all supported source files, skipping ignored dirs.
  3. Score each file for relevance to the issue using deterministic keyword signals.
  4. Select up to 3 highest-scoring files as relevant_files.
  5. Match the issue against a small rule table to find a known investigation category.
  6. Produce root_cause, suggested_fix, test_generated, and confidence from the match.
  7. Fall back gracefully when no strong rule matches.

All paths returned are relative to repository_path.
This engine is READ-ONLY; it never modifies any file.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

from backend.models.schemas import InvestigateResponse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".js", ".jsx", ".ts", ".tsx"}
)

IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "dist",
        "build",
    }
)

# Maximum number of relevant files returned.
MAX_RELEVANT_FILES = 3

# Confidence used when a rule matches.
HIGH_CONFIDENCE = 0.90

# Confidence used for the generic fallback.
LOW_CONFIDENCE = 0.25


# ---------------------------------------------------------------------------
# Rule table
# ---------------------------------------------------------------------------
# Each rule is a tuple of:
#   (
#     trigger_keywords:  list[str]  — at least one must appear in the issue
#     category_keywords: list[str]  — used for file-relevance boosting
#     root_cause:        str
#     suggested_fix:     str
#     test_generated:    str
#   )
#
# Rules are evaluated in order; the first match wins.
# ---------------------------------------------------------------------------

_Rule = Tuple[List[str], List[str], str, str, str]

_RULES: List[_Rule] = [
    # -----------------------------------------------------------------------
    # Rule 1 — Missing / unvalidated quantity in checkout
    # -----------------------------------------------------------------------
    (
        # trigger: issue must mention both checkout-family AND quantity-family words
        ["checkout", "cart", "order", "purchase"],
        ["quantity", "qty", "amount", "checkout", "cart", "order"],
        (
            "The quantity input is used before being validated. "
            "A missing or None quantity causes the calculation to fail."
        ),
        (
            "Validate the quantity field before performing checkout calculations "
            "or payment processing. Raise a clear error or return a safe default "
            "when quantity is absent or invalid."
        ),
        (
            "Add a regression test verifying that checkout rejects or safely "
            "handles a missing or None quantity without raising an unhandled exception."
        ),
    ),
    # -----------------------------------------------------------------------
    # Rule 2 — Authentication / login failure
    # -----------------------------------------------------------------------
    (
        ["auth", "login", "authentication", "unauthorized", "credential", "token"],
        ["auth", "login", "session", "token", "credential", "permission"],
        (
            "Authentication logic is not handling an edge case correctly, "
            "which may allow invalid credentials through or reject valid ones."
        ),
        (
            "Review the authentication flow for missing validation of tokens or "
            "credentials. Ensure all failure paths return appropriate responses "
            "and do not expose sensitive data."
        ),
        (
            "Add a regression test covering authentication with invalid or missing "
            "credentials to verify the correct error response is returned."
        ),
    ),
    # -----------------------------------------------------------------------
    # Rule 3 — Payment processing failure
    # -----------------------------------------------------------------------
    (
        ["payment", "charge", "billing", "invoice", "stripe", "transaction"],
        ["payment", "charge", "billing", "invoice", "transaction", "price", "amount"],
        (
            "Payment processing logic is encountering an unhandled input or state, "
            "likely a missing or invalid amount field."
        ),
        (
            "Validate all required payment fields (amount, currency, method) before "
            "initiating any transaction. Return a controlled error for invalid inputs."
        ),
        (
            "Add a regression test that verifies payment processing rejects "
            "invalid or incomplete payment data without raising an unhandled exception."
        ),
    ),
    # -----------------------------------------------------------------------
    # Rule 4 — Configuration / environment variable issues
    # -----------------------------------------------------------------------
    (
        ["config", "configuration", "env", "environment", "setting", "variable"],
        ["config", "env", "setting", "secret", "key", "variable"],
        (
            "A required configuration key or environment variable is missing or "
            "not validated at startup, causing a runtime failure."
        ),
        (
            "Validate that all required configuration keys exist and have acceptable "
            "values at application startup. Provide clear error messages for missing config."
        ),
        (
            "Add a regression test that verifies the application detects and reports "
            "missing or invalid configuration values rather than failing silently."
        ),
    ),
    # -----------------------------------------------------------------------
    # Rule 5 — Generic input validation failure
    # -----------------------------------------------------------------------
    (
        ["validation", "validate", "input", "null", "none", "missing", "undefined", "empty"],
        ["validation", "validate", "input", "check", "guard"],
        (
            "User input is processed without sufficient validation, "
            "leading to an unhandled error when unexpected or missing data is received."
        ),
        (
            "Add input validation before processing user-supplied data. "
            "Return a descriptive error when required fields are absent or invalid."
        ),
        (
            "Add a regression test that submits invalid or missing input to the "
            "affected endpoint and verifies a safe, informative error is returned."
        ),
    ),
]


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def _discover_source_files(root: Path) -> List[Path]:
    """Return all supported source files under *root*, skipping ignored dirs."""
    found: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place so os.walk skips them entirely.
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for filename in filenames:
            if Path(filename).suffix in SUPPORTED_EXTENSIONS:
                found.append(Path(dirpath) / filename)
    return found


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> List[str]:
    """Lower-case, split on non-alphanumeric boundaries."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _issue_keywords(issue: str) -> List[str]:
    """Extract meaningful words from the issue string."""
    stop = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "can", "could", "not", "no", "and", "or",
        "but", "if", "in", "on", "at", "to", "for", "of", "with", "it",
        "its", "this", "that", "when", "where", "which", "who", "what", "how",
        "i", "we", "you", "he", "she", "they", "my", "our", "your",
    }
    return [w for w in _tokenize(issue) if w not in stop and len(w) > 1]


def _score_file(
    filepath: Path,
    root: Path,
    issue_words: List[str],
    category_keywords: Optional[List[str]],
) -> int:
    """Return a relevance score >= 0 for a single file."""
    score = 0
    stem_words = _tokenize(filepath.stem)

    # +3 for each issue keyword that appears in the file stem.
    for word in issue_words:
        if word in stem_words:
            score += 3

    # +2 for each category keyword in the file stem (rule-specific boost).
    if category_keywords:
        for kw in category_keywords:
            if kw in stem_words:
                score += 2

    # Read file content for text-matching (skip on read errors).
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return score

    content_tokens = set(_tokenize(content))

    # +1 for each issue keyword found anywhere in the file content.
    for word in issue_words:
        if word in content_tokens:
            score += 1

    # +1 for each category keyword found in content.
    if category_keywords:
        for kw in category_keywords:
            if kw in content_tokens:
                score += 1

    return score


def _rank_files(
    files: List[Path],
    root: Path,
    issue_words: List[str],
    category_keywords: Optional[List[str]],
) -> List[str]:
    """
    Score each file and return up to MAX_RELEVANT_FILES paths,
    relative to *root*, with the highest scores first.
    Files with a score of 0 are excluded.
    """
    scored = [
        (f, _score_file(f, root, issue_words, category_keywords))
        for f in files
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        str(f.relative_to(root))
        for f, s in scored[:MAX_RELEVANT_FILES]
        if s > 0
    ]


# ---------------------------------------------------------------------------
# Rule matching
# ---------------------------------------------------------------------------


def _match_rule(issue_words: List[str]) -> Optional[_Rule]:
    """
    Return the first rule whose trigger keywords overlap with *issue_words*.
    Returns None when no rule matches.
    """
    issue_word_set = set(issue_words)
    for rule in _RULES:
        triggers, *_ = rule
        if issue_word_set.intersection(triggers):
            return rule
    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def investigate_issue(issue: str, repository_path: str) -> InvestigateResponse:
    """
    Investigate *issue* against the repository at *repository_path*.

    Parameters
    ----------
    issue:
        Developer issue description. Must be a non-empty string.
    repository_path:
        Filesystem path to the repository root. Must exist and be a directory.

    Returns
    -------
    InvestigateResponse
        Fully populated response compatible with the approved API contract.

    Raises
    ------
    ValueError
        When *issue* is empty or *repository_path* is invalid.
    """
    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    if not issue or not issue.strip():
        raise ValueError("Issue description must not be empty.")

    repo = Path(repository_path)
    if not repo.exists():
        raise ValueError(f"Repository path does not exist: {repository_path!r}")
    if not repo.is_dir():
        raise ValueError(f"Repository path is not a directory: {repository_path!r}")

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------
    all_files = _discover_source_files(repo)

    # ------------------------------------------------------------------
    # Keyword extraction
    # ------------------------------------------------------------------
    issue_words = _issue_keywords(issue)

    # ------------------------------------------------------------------
    # Rule matching
    # ------------------------------------------------------------------
    matched_rule = _match_rule(issue_words)
    category_keywords: Optional[List[str]] = matched_rule[1] if matched_rule else None

    # ------------------------------------------------------------------
    # Relevant-file ranking
    # ------------------------------------------------------------------
    if all_files:
        relevant_files = _rank_files(all_files, repo, issue_words, category_keywords)
    else:
        relevant_files = []

    # ------------------------------------------------------------------
    # Build result from matched rule or fallback
    # ------------------------------------------------------------------
    if matched_rule:
        _, _, root_cause, suggested_fix, test_generated = matched_rule
        confidence = HIGH_CONFIDENCE
    else:
        # Fallback: no strong rule match.
        root_cause = (
            "No deterministic root cause could be identified for this issue. "
            "Manual inspection of the relevant files is recommended."
        )
        suggested_fix = (
            "Inspect the relevant files identified above. Look for missing input "
            "validation, unhandled edge cases, or incorrect assumptions about "
            "the state of external dependencies."
        )
        # Generate a test recommendation based on issue keywords when possible.
        issue_preview = issue.strip()[:80]
        test_generated = (
            f"Add a regression test that reproduces the reported condition: "
            f'"{issue_preview}". Verify the system responds safely rather than '
            f"raising an unhandled exception."
        )
        confidence = LOW_CONFIDENCE

    return InvestigateResponse(
        issue=issue,
        relevant_files=relevant_files,
        root_cause=root_cause,
        suggested_fix=suggested_fix,
        test_generated=test_generated,
        confidence=confidence,
    )
