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


# ---------------------------------------------------------------------------
# Task 07 — Regression-Test Recommendation Workflow tests
# ---------------------------------------------------------------------------
# These tests verify that _build_regression_test_recommendation() (and the
# end-to-end investigate_issue() integration that calls it) produces concrete,
# actionable, deterministic recommendations for every recognised category and
# for the generic fallback path.
# All assertions operate only on the returned InvestigateResponse object;
# no analysed repository file is modified in any of these tests.
# ---------------------------------------------------------------------------


from backend.services.investigation import _build_regression_test_recommendation  # noqa: E402


class TestRegressionTestRecommendationWorkflow:
    """
    Focused tests for the enhanced regression-test recommendation workflow
    introduced in Task 07.
    """

    # ------------------------------------------------------------------
    # Fixtures (temporary repos created per-test via _make_repo)
    # ------------------------------------------------------------------

    def setup_method(self):
        # A minimal repo with one Python file — enough for the engine to
        # accept any repository_path argument without raising ValueError.
        self.tmp = _make_repo(("app.py", "# placeholder\n"))
        self.repo = self.tmp.name

    def teardown_method(self):
        self.tmp.cleanup()

    # ------------------------------------------------------------------
    # Helper: call investigate_issue and return the result
    # ------------------------------------------------------------------

    def _run(self, issue: str) -> InvestigateResponse:
        return investigate_issue(issue, self.repo)

    # ------------------------------------------------------------------
    # 1. Category-specific recommendations
    # ------------------------------------------------------------------

    def test_checkout_recommendation_is_concrete(self):
        """Checkout issue → recommendation mentions quantity and assertion."""
        result = self._run("Checkout crashes when quantity is missing.")
        rec = result.test_generated.lower()
        # Must mention what to test
        assert "checkout" in rec or "quantity" in rec, (
            f"Expected 'checkout' or 'quantity' in recommendation, got: {result.test_generated!r}"
        )
        # Must mention an assertion
        assert "assert" in rec, (
            f"Expected 'assert' in checkout recommendation, got: {result.test_generated!r}"
        )

    def test_checkout_recommendation_mentions_none_or_missing(self):
        """Checkout recommendation must specify None/omitted quantity as the edge case."""
        result = self._run("Checkout fails when quantity is None.")
        rec = result.test_generated.lower()
        assert "none" in rec or "omit" in rec or "missing" in rec, (
            f"Expected None/omit/missing edge case in: {result.test_generated!r}"
        )

    def test_checkout_recommendation_mentions_validation_error(self):
        """Checkout recommendation must describe the expected behaviour (validation error)."""
        result = self._run("Cart total calculation crashes when order has no quantity.")
        rec = result.test_generated.lower()
        assert "validation error" in rec or "rejected" in rec or "reject" in rec, (
            f"Expected rejected/validation error in: {result.test_generated!r}"
        )

    def test_authentication_recommendation_is_concrete(self):
        """Auth issue → recommendation mentions credentials/token and expected failure."""
        result = self._run("Login fails with an invalid token.")
        rec = result.test_generated.lower()
        assert "credential" in rec or "token" in rec or "password" in rec, (
            f"Expected credential/token in auth recommendation, got: {result.test_generated!r}"
        )
        assert "assert" in rec, (
            f"Expected 'assert' in auth recommendation, got: {result.test_generated!r}"
        )

    def test_authentication_recommendation_mentions_invalid_input(self):
        """Auth recommendation must describe invalid or blank credentials as the edge case."""
        result = self._run("Authentication fails with expired credentials.")
        rec = result.test_generated.lower()
        assert (
            "invalid" in rec
            or "blank" in rec
            or "expired" in rec
            or "missing" in rec
        ), (
            f"Expected invalid/blank/expired edge case in: {result.test_generated!r}"
        )

    def test_authentication_recommendation_mentions_expected_response(self):
        """Auth recommendation must describe the expected outcome (no valid session issued)."""
        result = self._run("Unauthorized access possible when token is missing.")
        rec = result.test_generated.lower()
        assert "session" in rec or "error" in rec or "rejected" in rec or "reject" in rec, (
            f"Expected session/error/rejected in: {result.test_generated!r}"
        )

    def test_payment_recommendation_is_concrete(self):
        """Payment issue → recommendation mentions amount and assertion."""
        result = self._run("Payment processing fails when charge amount is zero.")
        rec = result.test_generated.lower()
        assert "amount" in rec or "payment" in rec or "charge" in rec, (
            f"Expected amount/payment/charge in recommendation, got: {result.test_generated!r}"
        )
        assert "assert" in rec, (
            f"Expected 'assert' in payment recommendation, got: {result.test_generated!r}"
        )

    def test_payment_recommendation_mentions_invalid_amounts(self):
        """Payment recommendation must list specific invalid inputs (None, zero, negative)."""
        result = self._run("Billing crashes when invoice has no amount.")
        rec = result.test_generated.lower()
        assert "none" in rec or "zero" in rec or "negative" in rec or "missing" in rec, (
            f"Expected None/zero/negative edge case in: {result.test_generated!r}"
        )

    def test_payment_recommendation_mentions_no_external_call(self):
        """Payment recommendation must note that no external processor should be contacted."""
        result = self._run("Stripe transaction raises unhandled error.")
        rec = result.test_generated.lower()
        assert "external" in rec or "processor" in rec or "transaction" in rec, (
            f"Expected external/processor/transaction guard in: {result.test_generated!r}"
        )

    def test_configuration_recommendation_is_concrete(self):
        """Config issue → recommendation mentions environment variable and startup assertion."""
        result = self._run("Missing environment variable causes a runtime crash.")
        rec = result.test_generated.lower()
        assert "configuration" in rec or "environment" in rec or "variable" in rec or "key" in rec, (
            f"Expected configuration/environment/variable in recommendation, got: {result.test_generated!r}"
        )
        assert "assert" in rec, (
            f"Expected 'assert' in configuration recommendation, got: {result.test_generated!r}"
        )

    def test_configuration_recommendation_mentions_startup(self):
        """Config recommendation must reference startup or initialisation."""
        result = self._run("App fails on startup due to missing config setting.")
        rec = result.test_generated.lower()
        assert "startup" in rec or "start" in rec or "initialise" in rec or "initializ" in rec, (
            f"Expected startup/initialise in: {result.test_generated!r}"
        )

    def test_configuration_recommendation_mentions_silent_failure(self):
        """Config recommendation must contrast with silent failure."""
        result = self._run("Config variable is not checked, app crashes silently.")
        rec = result.test_generated.lower()
        assert "silently" in rec or "silent" in rec or "descriptive" in rec or "clear" in rec, (
            f"Expected silent/descriptive/clear in: {result.test_generated!r}"
        )

    def test_input_validation_recommendation_is_concrete(self):
        """Input-validation issue → recommendation mentions None/empty and assertion."""
        result = self._run("Input validation fails when field is missing.")
        rec = result.test_generated.lower()
        assert "none" in rec or "empty" in rec or "invalid" in rec, (
            f"Expected None/empty/invalid in validation recommendation, got: {result.test_generated!r}"
        )
        assert "assert" in rec, (
            f"Expected 'assert' in input_validation recommendation, got: {result.test_generated!r}"
        )

    def test_input_validation_recommendation_mentions_business_logic(self):
        """Validation recommendation must say logic is reached only after validation."""
        result = self._run("Null input causes error before processing.")
        rec = result.test_generated.lower()
        assert "business logic" in rec or "persistence" in rec or "before" in rec, (
            f"Expected business logic/persistence/before in: {result.test_generated!r}"
        )

    def test_input_validation_recommendation_mentions_descriptive_error(self):
        """Validation recommendation must describe a descriptive error response."""
        result = self._run("None value passed to validation endpoint.")
        rec = result.test_generated.lower()
        assert "descriptive" in rec or "error" in rec, (
            f"Expected descriptive/error in: {result.test_generated!r}"
        )

    # ------------------------------------------------------------------
    # 2. Fallback recommendation
    # ------------------------------------------------------------------

    def test_fallback_recommendation_is_nonempty(self):
        """Unknown issue → fallback recommendation is still non-empty."""
        result = self._run("xyzzy frobnicate wibble grault")
        assert len(result.test_generated.strip()) > 0

    def test_fallback_recommendation_is_useful(self):
        """Fallback recommendation must describe reproducing and asserting safe outcome."""
        result = self._run("xyzzy frobnicate wibble grault")
        rec = result.test_generated.lower()
        assert "assert" in rec or "safe" in rec or "controlled" in rec, (
            f"Expected assert/safe/controlled in fallback: {result.test_generated!r}"
        )

    def test_fallback_recommendation_includes_issue_context(self):
        """Fallback must echo back the issue description for context."""
        issue = "xyzzy frobnicate wibble grault"
        result = self._run(issue)
        # The first 80 chars of the issue should appear in the recommendation.
        assert issue[:40] in result.test_generated, (
            f"Expected issue text in fallback, got: {result.test_generated!r}"
        )

    def test_fallback_does_not_invent_category_details(self):
        """Fallback must not contain category-specific jargon (checkout, payment, etc.)."""
        result = self._run("xyzzy frobnicate wibble grault")
        rec = result.test_generated.lower()
        # None of the category-specific concrete terms should appear in a pure fallback.
        category_terms = {"checkout", "quantity", "credential", "token", "payment", "charge"}
        found = category_terms.intersection(rec.split())
        assert not found, (
            f"Fallback recommendation should not contain category-specific terms {found}, "
            f"got: {result.test_generated!r}"
        )

    # ------------------------------------------------------------------
    # 3. Determinism
    # ------------------------------------------------------------------

    def test_checkout_recommendation_is_deterministic(self):
        """Running the same checkout issue twice produces the exact same recommendation."""
        issue = "Checkout crashes when quantity is missing."
        r1 = investigate_issue(issue, self.repo)
        r2 = investigate_issue(issue, self.repo)
        assert r1.test_generated == r2.test_generated

    def test_auth_recommendation_is_deterministic(self):
        """Auth issue → deterministic recommendation."""
        issue = "Login fails with expired token."
        r1 = investigate_issue(issue, self.repo)
        r2 = investigate_issue(issue, self.repo)
        assert r1.test_generated == r2.test_generated

    def test_fallback_recommendation_is_deterministic(self):
        """Fallback path → deterministic recommendation."""
        issue = "xyzzy frobnicate wibble grault"
        r1 = investigate_issue(issue, self.repo)
        r2 = investigate_issue(issue, self.repo)
        assert r1.test_generated == r2.test_generated

    # ------------------------------------------------------------------
    # 4. test_generated remains a string
    # ------------------------------------------------------------------

    def test_checkout_test_generated_is_str(self):
        result = self._run("Checkout crashes when quantity is missing.")
        assert isinstance(result.test_generated, str)

    def test_auth_test_generated_is_str(self):
        result = self._run("Login fails with an invalid token.")
        assert isinstance(result.test_generated, str)

    def test_payment_test_generated_is_str(self):
        result = self._run("Payment processing fails when charge is None.")
        assert isinstance(result.test_generated, str)

    def test_config_test_generated_is_str(self):
        result = self._run("Missing config environment variable causes crash.")
        assert isinstance(result.test_generated, str)

    def test_validation_test_generated_is_str(self):
        result = self._run("Validation fails on null input.")
        assert isinstance(result.test_generated, str)

    def test_fallback_test_generated_is_str(self):
        result = self._run("xyzzy frobnicate wibble grault")
        assert isinstance(result.test_generated, str)

    # ------------------------------------------------------------------
    # 5. API contract: confidence is float within [0.0, 1.0]
    # ------------------------------------------------------------------

    def test_confidence_is_float_for_all_categories(self):
        issues = [
            "Checkout crashes when quantity is missing.",
            "Login fails with an invalid token.",
            "Payment charge fails with no amount.",
            "Missing env variable causes configuration crash.",
            "Null input causes validation error.",
            "xyzzy frobnicate wibble grault",
        ]
        for issue in issues:
            result = self._run(issue)
            assert isinstance(result.confidence, float), (
                f"confidence is not float for issue: {issue!r}"
            )
            assert 0.0 <= result.confidence <= 1.0, (
                f"confidence {result.confidence} out of bounds for: {issue!r}"
            )

    # ------------------------------------------------------------------
    # 6. No analysed repository files are modified
    # ------------------------------------------------------------------

    def test_analysed_repo_files_not_modified(self):
        """
        investigate_issue must be strictly READ-ONLY — no file in the
        analysed repository may be modified.
        """
        source = "checkout.py"
        original_content = "def checkout(cart, quantity):\n    return cart['price'] * quantity\n"
        tmp = _make_repo((source, original_content))
        try:
            investigate_issue(
                "Checkout crashes when quantity is missing.",
                tmp.name,
            )
            actual_content = (Path(tmp.name) / source).read_text(encoding="utf-8")
            assert actual_content == original_content, (
                f"Repository file was modified by investigate_issue! "
                f"Expected:\n{original_content!r}\nGot:\n{actual_content!r}"
            )
        finally:
            tmp.cleanup()

    def test_no_new_files_written_to_repo(self):
        """
        investigate_issue must not write any new files into the analysed
        repository directory.
        """
        source = "app.py"
        tmp = _make_repo((source, "# placeholder\n"))
        try:
            files_before = set(Path(tmp.name).rglob("*"))
            investigate_issue(
                "xyzzy frobnicate wibble grault",
                tmp.name,
            )
            files_after = set(Path(tmp.name).rglob("*"))
            new_files = files_after - files_before
            assert not new_files, (
                f"investigate_issue created unexpected files: {new_files}"
            )
        finally:
            tmp.cleanup()

    # ------------------------------------------------------------------
    # 7. InvestigateResponse schema is unchanged
    # ------------------------------------------------------------------

    def test_response_has_all_required_schema_fields(self):
        """InvestigateResponse must still have all six required fields."""
        result = self._run("Checkout crashes when quantity is missing.")
        data = result.model_dump()
        required = {"issue", "relevant_files", "root_cause", "suggested_fix", "test_generated", "confidence"}
        assert required.issubset(set(data.keys()))

    def test_response_passes_pydantic_reconstruction(self):
        """A round-tripped InvestigateResponse must still validate without error."""
        result = self._run("Checkout crashes when quantity is missing.")
        reconstructed = InvestigateResponse(**result.model_dump())
        assert reconstructed.test_generated == result.test_generated

    def test_response_serialises_test_generated_as_string(self):
        """JSON serialisation must emit test_generated as a JSON string."""
        import json
        result = self._run("Checkout crashes when quantity is missing.")
        raw = result.model_dump_json()
        parsed = json.loads(raw)
        assert isinstance(parsed["test_generated"], str)

    # ------------------------------------------------------------------
    # 8. _build_regression_test_recommendation unit tests
    # ------------------------------------------------------------------

    def test_helper_checkout_returns_known_template(self):
        """Direct unit test: checkout category returns a concrete template."""
        rec = _build_regression_test_recommendation("checkout", "any issue")
        assert "quantity" in rec.lower()
        assert "assert" in rec.lower()

    def test_helper_authentication_returns_known_template(self):
        rec = _build_regression_test_recommendation("authentication", "any issue")
        assert "credential" in rec.lower() or "token" in rec.lower()
        assert "assert" in rec.lower()

    def test_helper_payment_returns_known_template(self):
        rec = _build_regression_test_recommendation("payment", "any issue")
        assert "amount" in rec.lower()
        assert "assert" in rec.lower()

    def test_helper_configuration_returns_known_template(self):
        rec = _build_regression_test_recommendation("configuration", "any issue")
        assert "configuration" in rec.lower() or "environment" in rec.lower()
        assert "assert" in rec.lower()

    def test_helper_input_validation_returns_known_template(self):
        rec = _build_regression_test_recommendation("input_validation", "any issue")
        assert "none" in rec.lower() or "empty" in rec.lower()
        assert "assert" in rec.lower()

    def test_helper_none_category_uses_fallback(self):
        """None category triggers the fallback path and includes issue text."""
        issue = "xyzzy frobnicate wibble"
        rec = _build_regression_test_recommendation(None, issue)
        assert issue in rec
        assert len(rec) > 0

    def test_helper_unknown_category_uses_fallback(self):
        """Unrecognised category string falls back gracefully."""
        issue = "something unusual happened"
        rec = _build_regression_test_recommendation("nonexistent_category", issue)
        # Unknown categories should still produce a useful non-empty string.
        assert len(rec.strip()) > 0
        # And it should mention the issue
        assert issue in rec

    def test_helper_returns_str_type(self):
        for category in ["checkout", "authentication", "payment", "configuration", "input_validation", None]:
            rec = _build_regression_test_recommendation(category, "some issue text")
            assert isinstance(rec, str), f"Expected str for category={category!r}, got {type(rec)}"

    def test_helper_is_deterministic(self):
        """Calling the helper twice with the same args returns the same string."""
        for category in ["checkout", "authentication", "payment", "configuration", "input_validation", None]:
            r1 = _build_regression_test_recommendation(category, "some issue text")
            r2 = _build_regression_test_recommendation(category, "some issue text")
            assert r1 == r2, f"Non-deterministic for category={category!r}"
