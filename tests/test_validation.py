"""
Tests for backend/services/validation.py

Covers:
  SERVICE:
  1.  Successful pytest run (all tests pass) — correct counts, status="passed"
  2.  Failing pytest run — correct counts, status="failed"
  3.  Correct test counts for mixed pass/fail
  4.  status="passed" when returncode=0
  5.  status="failed" when returncode=1
  6.  Missing repository path — status="error"
  7.  Repository path is not a directory (file supplied) — still accepted (file is valid)
  8.  Timeout behavior — status="error"
  9.  subprocess execution error (OSError) — status="error"
  10. No arbitrary shell execution — shell=False enforced
  11. No tests discovered (exit code 5) — status="error"
  12. Unparseable output — status="error"
  13. Zero tests path (empty output but returncode 0) — handled safely
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.models.schemas import ValidateResponse
from backend.services.validation import _parse_counts, run_validation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_dir(*files: tuple[str, str]) -> tempfile.TemporaryDirectory:
    """
    Create a temporary directory with the given (relative_path, content) test files.
    Caller is responsible for cleanup.
    """
    tmp = tempfile.TemporaryDirectory()
    for rel_path, content in files:
        target = Path(tmp.name) / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tmp


_PASSING_TEST = "def test_always_passes():\n    assert 1 + 1 == 2\n"

_FAILING_TEST = (
    "def test_always_fails():\n"
    "    assert False, 'intentional failure'\n"
)

_MIXED_TEST = (
    "def test_pass():\n"
    "    assert True\n"
    "\n"
    "def test_fail():\n"
    "    assert False\n"
)


# ---------------------------------------------------------------------------
# Test 1 — Successful pytest run returns correct counts and status="passed"
# ---------------------------------------------------------------------------


class TestSuccessfulRun:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_passing.py", _PASSING_TEST))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_returns_validate_response(self):
        result = run_validation(self.tmp.name)
        assert isinstance(result, ValidateResponse)

    def test_status_is_passed(self):
        result = run_validation(self.tmp.name)
        assert result.status == "passed"

    def test_passed_count_is_correct(self):
        result = run_validation(self.tmp.name)
        assert result.passed == 1

    def test_failed_count_is_zero(self):
        result = run_validation(self.tmp.name)
        assert result.failed == 0

    def test_tests_run_is_correct(self):
        result = run_validation(self.tmp.name)
        assert result.tests_run == 1


# ---------------------------------------------------------------------------
# Test 2 — Failing pytest run returns status="failed"
# ---------------------------------------------------------------------------


class TestFailingRun:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_failing.py", _FAILING_TEST))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_returns_validate_response(self):
        result = run_validation(self.tmp.name)
        assert isinstance(result, ValidateResponse)

    def test_status_is_failed(self):
        result = run_validation(self.tmp.name)
        assert result.status == "failed"

    def test_failed_count_is_nonzero(self):
        result = run_validation(self.tmp.name)
        assert result.failed == 1

    def test_passed_count_is_zero(self):
        result = run_validation(self.tmp.name)
        assert result.passed == 0

    def test_tests_run_is_correct(self):
        result = run_validation(self.tmp.name)
        assert result.tests_run == 1


# ---------------------------------------------------------------------------
# Test 3 — Mixed pass/fail run returns correct counts
# ---------------------------------------------------------------------------


class TestMixedRun:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_mixed.py", _MIXED_TEST))

    def teardown_method(self):
        self.tmp.cleanup()

    def test_status_is_failed(self):
        result = run_validation(self.tmp.name)
        assert result.status == "failed"

    def test_passed_count(self):
        result = run_validation(self.tmp.name)
        assert result.passed == 1

    def test_failed_count(self):
        result = run_validation(self.tmp.name)
        assert result.failed == 1

    def test_tests_run_is_sum(self):
        result = run_validation(self.tmp.name)
        assert result.tests_run == result.passed + result.failed


# ---------------------------------------------------------------------------
# Test 4 & 5 — status derived from pytest return code, not magic strings
# ---------------------------------------------------------------------------


class TestStatusFromReturnCode:
    def test_returncode_0_gives_passed(self):
        """Mocked subprocess — exit code 0 → status='passed'."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed in 0.01s\n"
        mock_result.stderr = ""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.status == "passed"

    def test_returncode_1_gives_failed(self):
        """Mocked subprocess — exit code 1 → status='failed'."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "1 failed in 0.01s\n"
        mock_result.stderr = ""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_FAILING_TEST)
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.status == "failed"

    def test_returncode_2_gives_error(self):
        """Exit code 2 (interrupted) → status='error'."""
        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stdout = "1 passed in 0.01s\n"
        mock_result.stderr = ""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.status == "error"

    def test_returncode_3_gives_error(self):
        """Exit code 3 (internal error) → status='error'."""
        mock_result = MagicMock()
        mock_result.returncode = 3
        mock_result.stdout = ""
        mock_result.stderr = "internal error"
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.status == "error"


# ---------------------------------------------------------------------------
# Test 6 — Missing repository path → status="error"
# ---------------------------------------------------------------------------


class TestMissingRepositoryPath:
    def test_nonexistent_path_returns_error(self):
        result = run_validation("/nonexistent/path/that/does/not/exist/xyzzy")
        assert isinstance(result, ValidateResponse)

    def test_nonexistent_path_status_is_error(self):
        result = run_validation("/nonexistent/path/that/does/not/exist/xyzzy")
        assert result.status == "error"

    def test_nonexistent_path_counts_are_zero(self):
        result = run_validation("/nonexistent/path/that/does/not/exist/xyzzy")
        assert result.tests_run == 0
        assert result.passed == 0
        assert result.failed == 0

    def test_nonexistent_path_does_not_raise(self):
        """Must not raise any exception for missing path."""
        try:
            run_validation("/nonexistent/xyzzy/path")
        except Exception as exc:
            pytest.fail(f"run_validation raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# Test 7 — Path is a file (not a directory) — pytest can target a file too
# ---------------------------------------------------------------------------


class TestFilePathTarget:
    def setup_method(self):
        self.tmp = _make_test_dir(("test_passing.py", _PASSING_TEST))
        self.test_file = str(Path(self.tmp.name) / "test_passing.py")

    def teardown_method(self):
        self.tmp.cleanup()

    def test_file_target_runs_successfully(self):
        """A direct file path is a valid pytest target."""
        result = run_validation(self.test_file)
        assert isinstance(result, ValidateResponse)
        assert result.status == "passed"

    def test_file_target_correct_counts(self):
        result = run_validation(self.test_file)
        assert result.passed == 1
        assert result.failed == 0


# ---------------------------------------------------------------------------
# Test 8 — Timeout behavior → status="error"
# ---------------------------------------------------------------------------


class TestTimeoutBehavior:
    def test_timeout_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=60),
            ):
                result = run_validation(tmp)
        assert isinstance(result, ValidateResponse)
        assert result.status == "error"

    def test_timeout_counts_are_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=60),
            ):
                result = run_validation(tmp)
        assert result.tests_run == 0
        assert result.passed == 0
        assert result.failed == 0

    def test_timeout_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=60),
            ):
                try:
                    run_validation(tmp)
                except Exception as exc:
                    pytest.fail(f"run_validation raised on timeout: {exc}")


# ---------------------------------------------------------------------------
# Test 9 — subprocess OSError → status="error"
# ---------------------------------------------------------------------------


class TestSubprocessExecutionError:
    def test_oserror_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", side_effect=OSError("pytest not found")):
                result = run_validation(tmp)
        assert isinstance(result, ValidateResponse)
        assert result.status == "error"

    def test_oserror_counts_are_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", side_effect=OSError("pytest not found")):
                result = run_validation(tmp)
        assert result.tests_run == 0
        assert result.passed == 0
        assert result.failed == 0

    def test_oserror_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", side_effect=OSError("pytest not found")):
                try:
                    run_validation(tmp)
                except Exception as exc:
                    pytest.fail(f"run_validation raised on OSError: {exc}")


# ---------------------------------------------------------------------------
# Test 10 — No arbitrary shell execution — shell=False enforced
# ---------------------------------------------------------------------------


class TestNoArbitraryShellExecution:
    def test_subprocess_called_without_shell(self):
        """subprocess.run must be called with shell=False (or shell not set to True)."""
        captured_calls = []

        original_run = subprocess.run

        def capturing_run(*args, **kwargs):
            captured_calls.append(kwargs)
            return original_run(*args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", side_effect=capturing_run):
                run_validation(tmp)

        assert captured_calls, "subprocess.run was never called"
        for call_kwargs in captured_calls:
            assert call_kwargs.get("shell") is not True, (
                "subprocess.run was called with shell=True — this is a security violation"
            )

    def test_cmd_is_a_list_not_a_string(self):
        """The command must be a list so the shell never interprets it."""
        captured_cmds = []

        def capturing_run(cmd, *args, **kwargs):
            captured_cmds.append(cmd)
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = "1 passed in 0.01s\n"
            mock.stderr = ""
            return mock

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", side_effect=capturing_run):
                run_validation(tmp)

        assert captured_cmds, "subprocess.run was never called"
        for cmd in captured_cmds:
            assert isinstance(cmd, list), (
                f"Command must be a list, got {type(cmd)}: {cmd!r}"
            )


# ---------------------------------------------------------------------------
# Test 11 — No tests collected (exit code 5) → status="error"
# ---------------------------------------------------------------------------


class TestNoTestsCollected:
    def test_exit_code_5_returns_error(self):
        mock_result = MagicMock()
        mock_result.returncode = 5
        mock_result.stdout = "no tests ran\n"
        mock_result.stderr = ""
        with tempfile.TemporaryDirectory() as tmp:
            # No test files — pytest exit code 5
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.status == "error"

    def test_exit_code_5_counts_zero(self):
        mock_result = MagicMock()
        mock_result.returncode = 5
        mock_result.stdout = "no tests ran\n"
        mock_result.stderr = ""
        with tempfile.TemporaryDirectory() as tmp:
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.tests_run == 0
        assert result.passed == 0
        assert result.failed == 0


# ---------------------------------------------------------------------------
# Test 12 — Unparseable output → status="error"
# ---------------------------------------------------------------------------


class TestUnparseableOutput:
    def test_garbage_output_returns_error(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "xyzzy frobozz magic\n"
        mock_result.stderr = ""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.status == "error"

    def test_empty_output_returns_error(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_x.py").write_text(_PASSING_TEST)
            with patch("subprocess.run", return_value=mock_result):
                result = run_validation(tmp)
        assert result.status == "error"


# ---------------------------------------------------------------------------
# Test 13 — _parse_counts unit tests (internal helper)
# ---------------------------------------------------------------------------


class TestParseCountsHelper:
    def test_parse_all_passed(self):
        output = "test_foo.py ...\n1 passed in 0.03s\n"
        result = _parse_counts(output)
        assert result == (1, 0)

    def test_parse_all_failed(self):
        output = "test_foo.py F\n1 failed in 0.03s\n"
        result = _parse_counts(output)
        assert result == (0, 1)

    def test_parse_mixed(self):
        # pytest may emit either order; test both orderings.
        for line in [
            "1 passed, 1 failed in 0.05s",
            "1 failed, 1 passed in 0.05s",
        ]:
            result = _parse_counts(f"test_foo.py .F\n{line}\n")
            assert result == (1, 1), f"Failed for line: {line!r}"

    def test_parse_multiple_passed(self):
        output = "...\n5 passed in 0.12s\n"
        result = _parse_counts(output)
        assert result == (5, 0)

    def test_parse_multiple_failed(self):
        output = "FFF\n3 failed in 0.04s\n"
        result = _parse_counts(output)
        assert result == (0, 3)

    def test_parse_no_tests(self):
        output = "no tests ran\n"
        result = _parse_counts(output)
        assert result == (0, 0)

    def test_parse_empty_string_returns_none(self):
        result = _parse_counts("")
        assert result is None

    def test_parse_garbage_returns_none(self):
        result = _parse_counts("random text with no test counts\n")
        assert result is None

    def test_tests_run_equals_passed_plus_failed(self):
        output = "2 passed, 3 failed in 0.07s\n"
        result = _parse_counts(output)
        assert result is not None
        passed, failed = result
        assert passed + failed == 5
