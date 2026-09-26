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
x  6. Produce root_cause, suggested_fix, and confidence from the match.
  7. Build a concrete regression-test recommendation via
     _build_regression_test_recommendation().
  8. Fall back gracefully when no strong rule matches.

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
#     category:          str        — label used to build the test recommendation
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
        # trigger: issue must mention checkout-family words
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
        "checkout",
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
        "authentication",
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
        "payment",
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
        "configuration",
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
        "input_validation",
    ),
]


# ---------------------------------------------------------------------------
# Regression-test recommendation builder
# ---------------------------------------------------------------------------

# Per-category concrete recommendation templates.
# Each value is a complete, actionable string that explains:
#   (1) what behaviour to test,
#   (2) what input / edge case should trigger the test, and
#   (3) what expected outcome should be asserted.
_CATEGORY_RECOMMENDATIONS: dict = {
    "checkout": (
        "Add a regression test that calls the checkout function (or endpoint) "
        "with quantity=None and with quantity omitted entirely. "
        "Assert that the request is rejected with a clear validation error "
        "before any price calculation is attempted, and that no unhandled "
        "exception propagates to the caller."
    ),
    "authentication": (
        "Add a regression test that submits a login or token-verification "
        "request using an invalid credential (e.g. a blank password, an "
        "expired token, and a token with an invalid signature). "
        "Assert that each attempt is rejected with the correct authentication "
        "error response and that no valid session or token is issued."
    ),
    "payment": (
        "Add a regression test that invokes the payment or charge function "
        "with a missing amount (None), a zero amount, and a negative amount. "
        "Assert that each case is rejected with a controlled validation error "
        "before any external payment processor or transaction is contacted."
    ),
    "configuration": (
        "Add a regression test that starts (or initialises) the application "
        "with a required configuration key or environment variable removed. "
        "Assert that the application raises a clear, descriptive configuration "
        "error at startup rather than failing silently or crashing with an "
        "unrelated runtime exception later."
    ),
    "input_validation": (
        "Add a regression test that submits None, an empty string, and a "
        "structurally invalid value to the affected input field or endpoint. "
        "Assert that each submission is rejected with a descriptive validation "
        "error before any business logic or persistence layer is reached."
    ),
}


def _build_regression_test_recommendation(category: Optional[str], issue: str) -> str:
    """
    Return a concrete, deterministic regression-test recommendation string.

    Parameters
    ----------
    category:
        Investigation category label produced by the matched rule
        (e.g. ``"checkout"``, ``"authentication"``), or ``None`` for the
        generic fallback path.
    issue:
        The original issue description.  Used only in the fallback case to
        provide minimal context without inventing repository-specific details.

    Returns
    -------
    str
        A non-empty, human-readable recommendation that describes what
        behaviour to test, what input/edge case to use, and what outcome
        to assert.  Never returns an empty string.
    """
    if category is not None:
        recommendation = _CATEGORY_RECOMMENDATIONS.get(category)
        if recommendation:
            return recommendation

    # Generic fallback: quote up to 80 chars of the issue for context without
    # inventing details that were not discovered by the investigation engine.
    issue_preview = issue.strip()[:80]
    return (
        f'Add a regression test that reproduces the reported condition: '
        f'"{issue_preview}". '
        f"Supply the specific input or state that triggers the problem, "
        f"then assert that the system responds with a controlled, expected "
        f"outcome rather than raising an unhandled exception."
    )


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
        _, _, root_cause, suggested_fix, category = matched_rule
        confidence = HIGH_CONFIDENCE
    else:
        # Fallback: no strong rule match.
        category = None
        root_cause = (
            "No deterministic root cause could be identified for this issue. "
            "Manual inspection of the relevant files is recommended."
        )
        suggested_fix = (
            "Inspect the relevant files identified above. Look for missing input "
            "validation, unhandled edge cases, or incorrect assumptions about "
            "the state of external dependencies."
        )
        confidence = LOW_CONFIDENCE

    test_generated = _build_regression_test_recommendation(category, issue)

    return InvestigateResponse(
        issue=issue,
        relevant_files=relevant_files,
        root_cause=root_cause,
        suggested_fix=suggested_fix,
        test_generated=test_generated,
        confidence=confidence,
    )
