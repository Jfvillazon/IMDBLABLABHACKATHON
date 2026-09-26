"""
Tests for backend/services/investigation.py

All tests use temporary directories so the engine can be exercised
independently of the sample_repo/ contents or any teammate work.
No network access or external services required.

Covers the 12 required areas:
  1.  Checkout missing-quantity investigation
  2.  Wording variation for same issue
  3.  Relevant-file ranking
  4.  Repository-relative paths
  5.  Confidence within [0.0, 1.0]
  6.  Unknown-issue fallback
  7.  Nonexistent repository
  8.  Non-directory repository path
  9.  Empty issue
  10. Ignored directories not analysed
  11. No supported source files
  12. Compatibility with InvestigateResponse
"""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.models.schemas import InvestigateResponse
from backend.services.investigation import (
    IGNORED_DIRS,
    SUPPORTED_EXTENSIONS,
    investigate_issue,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(*files: tuple[str, str]) -> tempfile.TemporaryDirectory:
    """
    Create a temporary directory tree.
    *files* is a sequence of (relative_path, content) tuples.
    Returns the TemporaryDirectory object (caller is responsible for cleanup).
    """
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for rel, content in files:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp


# ---------------------------------------------------------------------------
# 1. Checkout missing-quantity investigation
# ---------------------------------------------------------------------------


class TestCheckoutMissingQuantity:
    """Primary demo scenario: checkout fails when quantity is missing."""

    def setup_method(self):
        self.tmp = _make_repo(
            (
                "checkout.py",
                "def process_checkout(cart):\n"
                "    total = cart['quantity'] * cart['price']\n"
                "    return total\n",
            ),
            (
                "utils.py",
                "def helper():\n    pass\n",
            ),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_checkout_file_identified(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert any("checkout" in f.lower() for f in result.relevant_files)

    def test_root_cause_mentions_quantity(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert "quantity" in result.root_cause.lower()

    def test_suggested_fix_mentions_validate(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert "validat" in result.suggested_fix.lower()

    def test_test_generated_is_nonempty_string(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert isinstance(result.test_generated, str)
        assert len(result.test_generated) > 0

    def test_confidence_is_high(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        # High-confidence rule match must be > 0.5
        assert result.confidence > 0.5

    def test_issue_echoed_back(self):
        issue = "Checkout crashes when quantity is missing."
        result = investigate_issue(issue, self.repo)
        assert result.issue == issue


# ---------------------------------------------------------------------------
# 2. Wording variations reach the same category
# ---------------------------------------------------------------------------


class TestCheckoutWordingVariations:
    """Different phrasings of the same checkout/quantity bug must match."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("checkout.py", "total = quantity * price\n"),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    @pytest.mark.parametrize(
        "issue",
        [
            "Checkout fails when quantity is None",
            "Missing quantity crashes checkout",
            "Checkout does not validate quantity",
            "Cart crashes if quantity not provided",
            "Order breaks without a quantity value",
        ],
    )
    def test_variation_returns_high_confidence(self, issue):
        result = investigate_issue(issue, self.repo)
        assert result.confidence > 0.5, (
            f"Expected high confidence for issue={issue!r}, got {result.confidence}"
        )

    @pytest.mark.parametrize(
        "issue",
        [
            "Checkout fails when quantity is None",
            "Missing quantity crashes checkout",
        ],
    )
    def test_variation_identifies_checkout_file(self, issue):
        result = investigate_issue(issue, self.repo)
        assert any("checkout" in f.lower() for f in result.relevant_files)


# ---------------------------------------------------------------------------
# 3. Relevant-file ranking
# ---------------------------------------------------------------------------


class TestRelevantFileRanking:
    """Files most related to the issue should rank above unrelated ones."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("checkout.py", "def checkout(cart): total = cart['quantity'] * cart['price']\n"),
            ("payment.py", "def pay(): pass\n"),
            ("logging_utils.py", "import logging\n"),
            ("unrelated_module.py", "def foo(): return 42\n"),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_checkout_file_is_first(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert result.relevant_files, "Expected at least one relevant file."
        assert "checkout.py" == result.relevant_files[0]

    def test_at_most_three_files_returned(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert len(result.relevant_files) <= 3

    def test_irrelevant_file_not_first(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        # logging_utils.py has no checkout/quantity keywords — should not be #1
        if result.relevant_files:
            assert result.relevant_files[0] != "logging_utils.py"


# ---------------------------------------------------------------------------
# 4. Repository-relative paths
# ---------------------------------------------------------------------------


class TestRepositoryRelativePaths:
    """Returned paths must be relative to repository_path, not absolute."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("src/checkout.py", "quantity = cart['qty']\n"),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_paths_are_relative(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        for f in result.relevant_files:
            assert not os.path.isabs(f), f"Path is absolute: {f!r}"

    def test_paths_do_not_start_with_repo_root(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        for f in result.relevant_files:
            assert not f.startswith(self.repo), (
                f"Path starts with repo root: {f!r}"
            )

    def test_nested_path_preserves_structure(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert any("src" in f for f in result.relevant_files)


# ---------------------------------------------------------------------------
# 5. Confidence within [0.0, 1.0]
# ---------------------------------------------------------------------------


class TestConfidenceBounds:
    """Confidence must always be a valid InvestigateResponse float."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("checkout.py", "# checkout logic\n"),
            ("random_module.py", "# unrelated\n"),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_high_confidence_in_bounds(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert 0.0 <= result.confidence <= 1.0

    def test_low_confidence_in_bounds(self):
        result = investigate_issue(
            "Completely obscure technical gibberish zxqwerty9999", self.repo
        )
        assert 0.0 <= result.confidence <= 1.0

    def test_confidence_validates_against_schema(self):
        """The confidence value must be accepted by InvestigateResponse."""
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        # This would raise ValidationError if confidence is out of [0, 1].
        InvestigateResponse(**result.model_dump())


# ---------------------------------------------------------------------------
# 6. Unknown issue fallback
# ---------------------------------------------------------------------------


class TestUnknownIssueFallback:
    """Unknown issues must return a safe low-confidence result, not crash."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("app.py", "def main(): pass\n"),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_unknown_issue_does_not_raise(self):
        # Should return gracefully, not raise.
        result = investigate_issue(
            "Zxqwerty unrecognised obscure failure mode zzz999", self.repo
        )
        assert isinstance(result, InvestigateResponse)

    def test_unknown_issue_returns_low_confidence(self):
        result = investigate_issue(
            "Zxqwerty unrecognised obscure failure mode zzz999", self.repo
        )
        assert result.confidence < 0.5

    def test_unknown_issue_has_nonempty_root_cause(self):
        result = investigate_issue(
            "Zxqwerty unrecognised obscure failure mode zzz999", self.repo
        )
        assert isinstance(result.root_cause, str) and len(result.root_cause) > 0

    def test_unknown_issue_has_nonempty_suggested_fix(self):
        result = investigate_issue(
            "Zxqwerty unrecognised obscure failure mode zzz999", self.repo
        )
        assert isinstance(result.suggested_fix, str) and len(result.suggested_fix) > 0

    def test_unknown_issue_has_nonempty_test_generated(self):
        result = investigate_issue(
            "Zxqwerty unrecognised obscure failure mode zzz999", self.repo
        )
        assert isinstance(result.test_generated, str) and len(result.test_generated) > 0

    def test_unknown_issue_result_validates_against_schema(self):
        result = investigate_issue(
            "Zxqwerty unrecognised obscure failure mode zzz999", self.repo
        )
        InvestigateResponse(**result.model_dump())


# ---------------------------------------------------------------------------
# 7. Nonexistent repository
# ---------------------------------------------------------------------------


class TestNonexistentRepository:
    """A path that does not exist must raise ValueError."""

    def test_nonexistent_path_raises_value_error(self):
        with pytest.raises(ValueError, match="does not exist"):
            investigate_issue(
                "Checkout crashes when quantity is missing.",
                "/nonexistent/path/that/cannot/possibly/exist/xyz123",
            )

    def test_nonexistent_path_does_not_raise_other_exception(self):
        try:
            investigate_issue("some issue", "/nonexistent/xyz")
        except ValueError:
            pass  # Expected
        except Exception as exc:
            pytest.fail(f"Unexpected exception type: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# 8. Non-directory repository path
# ---------------------------------------------------------------------------


class TestNonDirectoryRepositoryPath:
    """A file path (not a directory) must raise ValueError."""

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        self.tmp.write(b"# placeholder\n")
        self.tmp.close()

    def teardown_method(self):
        os.unlink(self.tmp.name)

    def test_file_path_raises_value_error(self):
        with pytest.raises(ValueError, match="not a directory"):
            investigate_issue("Checkout crashes", self.tmp.name)


# ---------------------------------------------------------------------------
# 9. Empty issue
# ---------------------------------------------------------------------------


class TestEmptyIssue:
    """Empty or whitespace-only issue must raise ValueError."""

    def setup_method(self):
        self.tmp = _make_repo(("app.py", "pass\n"))
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="[Ee]mpty|[Mm]ust not be empty"):
            investigate_issue("", self.repo)

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="[Ee]mpty|[Mm]ust not be empty"):
            investigate_issue("   ", self.repo)

    def test_tab_only_raises(self):
        with pytest.raises(ValueError, match="[Ee]mpty|[Mm]ust not be empty"):
            investigate_issue("\t\n", self.repo)


# ---------------------------------------------------------------------------
# 10. Ignored directories are not analysed
# ---------------------------------------------------------------------------


class TestIgnoredDirectories:
    """Files inside ignored dirs must not appear in results."""

    def setup_method(self):
        # Plant a checkout.py inside every ignored directory
        # and an unrelated one at the root so the repo is non-empty.
        files = [("app.py", "# real app\n")]
        for ignored_dir in IGNORED_DIRS:
            files.append(
                (
                    f"{ignored_dir}/checkout.py",
                    "# should be ignored\ntotal = quantity * price\n",
                )
            )
        self.tmp = _make_repo(*files)
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_ignored_files_not_in_relevant_files(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        for rel_path in result.relevant_files:
            parts = Path(rel_path).parts
            for ignored in IGNORED_DIRS:
                assert ignored not in parts, (
                    f"File from ignored directory appeared in results: {rel_path!r}"
                )

    def test_ignored_dir_checkout_does_not_appear(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        for rel_path in result.relevant_files:
            assert not rel_path.startswith(tuple(IGNORED_DIRS)), (
                f"Path starts with an ignored dir: {rel_path!r}"
            )


# ---------------------------------------------------------------------------
# 11. No supported source files
# ---------------------------------------------------------------------------


class TestNoSupportedSourceFiles:
    """Repository with only unsupported file types must not crash."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("README.md", "# project readme\n"),
            ("data.json", '{"key": "value"}\n'),
            ("image.png", b"\x89PNG placeholder".decode("latin-1")),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_no_source_files_returns_empty_relevant_files(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert result.relevant_files == []

    def test_no_source_files_does_not_crash(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert isinstance(result, InvestigateResponse)

    def test_confidence_in_bounds_with_no_files(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert 0.0 <= result.confidence <= 1.0


# ---------------------------------------------------------------------------
# 12. Compatibility with InvestigateResponse
# ---------------------------------------------------------------------------


class TestInvestigateResponseCompatibility:
    """Engine output must always be a valid InvestigateResponse."""

    def setup_method(self):
        self.tmp = _make_repo(
            ("checkout.py", "quantity = cart.get('qty')\ntotal = quantity * price\n"),
            ("auth.py", "token = request.headers.get('Authorization')\n"),
        )
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    def test_checkout_result_is_investigate_response_instance(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert isinstance(result, InvestigateResponse)

    def test_checkout_result_serializes_to_dict(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        data = result.model_dump()
        assert set(data.keys()) == {
            "issue",
            "relevant_files",
            "root_cause",
            "suggested_fix",
            "test_generated",
            "confidence",
        }

    def test_auth_result_is_investigate_response_instance(self):
        result = investigate_issue(
            "Login fails for valid users after token expiry.", self.repo
        )
        assert isinstance(result, InvestigateResponse)

    def test_fallback_result_is_investigate_response_instance(self):
        result = investigate_issue(
            "Zxqwerty unrecognised obscure failure zzz", self.repo
        )
        assert isinstance(result, InvestigateResponse)

    def test_result_passes_pydantic_reconstruction(self):
        """Serialize to dict and reconstruct — must not raise ValidationError."""
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        reconstructed = InvestigateResponse(**result.model_dump())
        assert reconstructed == result

    def test_relevant_files_is_list_of_strings(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert isinstance(result.relevant_files, list)
        for f in result.relevant_files:
            assert isinstance(f, str)

    def test_test_generated_is_str_not_bool(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert isinstance(result.test_generated, str)
        assert not isinstance(result.test_generated, bool)

    def test_confidence_is_float(self):
        result = investigate_issue(
            "Checkout crashes when quantity is missing.", self.repo
        )
        assert isinstance(result.confidence, float)


# ---------------------------------------------------------------------------
# Additional: supported extensions constant is sane
# ---------------------------------------------------------------------------


class TestConstants:
    def test_supported_extensions_non_empty(self):
        assert len(SUPPORTED_EXTENSIONS) >= 5

    def test_ignored_dirs_non_empty(self):
        assert len(IGNORED_DIRS) >= 6

    def test_git_in_ignored_dirs(self):
        assert ".git" in IGNORED_DIRS

    def test_node_modules_in_ignored_dirs(self):
        assert "node_modules" in IGNORED_DIRS
