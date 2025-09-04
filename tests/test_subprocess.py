"""Tests for safe subprocess execution utilities."""

import pytest
import subprocess
from unittest.mock import MagicMock, patch

from gh_actions_optimizer.shared.subprocess import (
    ALLOWED_COMMANDS,
    DEFAULT_TIMEOUT,
    MAX_ARG_LENGTH,
    SENSITIVE_PATTERNS,
    SubprocessSecurityError,
    check_command_availability,
    escape_argument,
    safe_gh_command,
    safe_git_command,
    safe_run,
    sanitize_for_logging,
    validate_arguments,
    validate_command,
)


class TestInputValidation:
    """Test input validation functions."""

    def test_validate_command_allowed(self) -> None:
        """Test validation of allowed commands."""
        for command in ALLOWED_COMMANDS:
            validate_command(command)  # Should not raise

    def test_validate_command_disallowed(self) -> None:
        """Test validation rejects disallowed commands."""
        with pytest.raises(
            SubprocessSecurityError, match="not in allowed list"
        ):
            validate_command("evil_command")

    def test_validate_command_empty(self) -> None:
        """Test validation rejects empty commands."""
        with pytest.raises(SubprocessSecurityError, match="Empty command"):
            validate_command("")

    def test_validate_arguments_valid(self) -> None:
        """Test validation of valid arguments."""
        validate_arguments(["gh", "repo", "view"])  # Should not raise

    def test_validate_arguments_empty(self) -> None:
        """Test validation rejects empty argument lists."""
        with pytest.raises(
            SubprocessSecurityError, match="Empty argument list"
        ):
            validate_arguments([])

    def test_validate_arguments_invalid_command(self) -> None:
        """Test validation rejects invalid commands in arguments."""
        with pytest.raises(
            SubprocessSecurityError, match="not in allowed list"
        ):
            validate_arguments(["rm", "-rf", "/"])

    def test_validate_arguments_non_string(self) -> None:
        """Test validation rejects non-string arguments."""
        with pytest.raises(SubprocessSecurityError, match="must be a string"):
            validate_arguments(["gh", 123])  # type: ignore

    def test_validate_arguments_too_long(self) -> None:
        """Test validation rejects overly long arguments."""
        long_arg = "x" * (MAX_ARG_LENGTH + 1)
        with pytest.raises(
            SubprocessSecurityError, match="exceeds maximum length"
        ):
            validate_arguments(["gh", long_arg])

    def test_validate_arguments_shell_chars_safe_context(self) -> None:
        """Test that shell characters are allowed in safe contexts."""
        # GitHub repo pattern
        validate_arguments(["gh", "repo", "view", "owner/repo"])

        # File extensions
        validate_arguments(["gh", "api", "path/to/file.yml"])

    def test_validate_arguments_shell_chars_logs_warning(self) -> None:
        """Test that shell characters in unsafe contexts log warnings."""
        with patch(
            "gh_actions_optimizer.shared.subprocess.log_warn"
        ) as mock_warn:
            validate_arguments(["gh", "echo", "$(evil_command)"])
            mock_warn.assert_called_once()


class TestSanitization:
    """Test sanitization functions."""

    def test_sanitize_for_logging_tokens(self) -> None:
        """Test sanitization removes tokens."""
        text = "Authorization: token ghp_1234567890abcdef"
        result = sanitize_for_logging(text)
        assert "[REDACTED]" in result
        assert "ghp_1234567890abcdef" not in result

    def test_sanitize_for_logging_passwords(self) -> None:
        """Test sanitization removes passwords."""
        text = "password=secret123"
        result = sanitize_for_logging(text)
        assert "[REDACTED]" in result
        assert "secret123" not in result

    def test_sanitize_for_logging_empty(self) -> None:
        """Test sanitization handles empty input."""
        assert sanitize_for_logging("") == ""
        assert sanitize_for_logging(None) is None  # type: ignore

    def test_sanitize_for_logging_no_sensitive_data(self) -> None:
        """Test sanitization preserves non-sensitive data."""
        text = "gh repo view owner/repo"
        result = sanitize_for_logging(text)
        assert result == text

    @pytest.mark.parametrize(
        "pattern,test_string",
        [
            (r"token[=:\s]+[a-zA-Z0-9_-]+", "token=abc123"),
            (r"gh[psu]_[a-zA-Z0-9_-]+", "ghp_abcdef123456"),
            (r"password[=:\s]+\S+", "password: mypass"),
            (r"secret[=:\s]+\S+", "secret=topsecret"),
            (r"key[=:\s]+[a-zA-Z0-9_/-]+", "key: ssh-rsa-abc123"),
        ],
    )
    def test_sensitive_patterns(self, pattern: str, test_string: str) -> None:
        """Test that sensitive patterns match expected strings."""
        import re

        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        assert compiled_pattern.search(test_string) is not None

    def test_escape_argument(self) -> None:
        """Test argument escaping."""
        # Safe argument should remain unchanged (except for quotes)
        safe_arg = "safe_argument"
        escaped = escape_argument(safe_arg)
        assert "safe_argument" in escaped

        # Dangerous argument should be quoted
        dangerous_arg = "arg; rm -rf /"
        escaped = escape_argument(dangerous_arg)
        assert "rm -rf" in escaped
        assert escaped.startswith("'") or escaped.startswith('"')


class TestSafeRun:
    """Test safe_run function."""

    @patch("subprocess.run")
    def test_safe_run_success(self, mock_run: MagicMock) -> None:
        """Test successful safe_run execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "version"], returncode=0, stdout="2.0.0", stderr=""
        )

        result = safe_run(["gh", "version"])

        assert result.returncode == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["gh", "version"]
        assert call_args[1]["shell"] is False
        assert call_args[1]["timeout"] == DEFAULT_TIMEOUT

    @patch("subprocess.run")
    def test_safe_run_with_timeout(self, mock_run: MagicMock) -> None:
        """Test safe_run with custom timeout."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "version"], returncode=0, stdout="2.0.0", stderr=""
        )

        safe_run(["gh", "version"], timeout=30)

        call_args = mock_run.call_args
        assert call_args[1]["timeout"] == 30

    @patch("subprocess.run")
    def test_safe_run_timeout_expired(self, mock_run: MagicMock) -> None:
        """Test safe_run handles timeout expiration."""
        mock_run.side_effect = subprocess.TimeoutExpired(["gh", "version"], 10)

        with pytest.raises(subprocess.TimeoutExpired):
            safe_run(["gh", "version"], timeout=10)

    @patch("subprocess.run")
    def test_safe_run_called_process_error(self, mock_run: MagicMock) -> None:
        """Test safe_run handles process errors."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["gh", "version"], stderr="command not found"
        )

        with pytest.raises(subprocess.CalledProcessError):
            safe_run(["gh", "version"])

    def test_safe_run_invalid_command(self) -> None:
        """Test safe_run rejects invalid commands."""
        with pytest.raises(SubprocessSecurityError):
            safe_run(["evil_command"])

    @patch("subprocess.run")
    def test_safe_run_forces_shell_false(self, mock_run: MagicMock) -> None:
        """Test that safe_run forces shell=False even if passed."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "version"], returncode=0, stdout="2.0.0", stderr=""
        )

        safe_run(["gh", "version"], shell=True)  # Should be overridden

        call_args = mock_run.call_args
        assert call_args[1]["shell"] is False


class TestSafeGitHubCommand:
    """Test safe GitHub CLI command execution."""

    @patch("gh_actions_optimizer.shared.subprocess.safe_run")
    def test_safe_gh_command(self, mock_safe_run: MagicMock) -> None:
        """Test safe_gh_command prepends 'gh' to arguments."""
        mock_safe_run.return_value = subprocess.CompletedProcess(
            args=["gh", "repo", "view"],
            returncode=0,
            stdout="result",
            stderr="",
        )

        safe_gh_command(["repo", "view"])

        mock_safe_run.assert_called_once_with(
            ["gh", "repo", "view"],
            timeout=None,
            check=True,
        )

    @patch("gh_actions_optimizer.shared.subprocess.safe_run")
    def test_safe_gh_command_with_options(
        self, mock_safe_run: MagicMock
    ) -> None:
        """Test safe_gh_command passes options correctly."""
        safe_gh_command(
            ["repo", "view"], timeout=60, check=False, capture_output=False
        )

        mock_safe_run.assert_called_once_with(
            ["gh", "repo", "view"],
            timeout=60,
            check=False,
            capture_output=False,
        )


class TestSafeGitCommand:
    """Test safe git command execution."""

    @patch("gh_actions_optimizer.shared.subprocess.safe_run")
    def test_safe_git_command(self, mock_safe_run: MagicMock) -> None:
        """Test safe_git_command prepends 'git' to arguments."""
        mock_safe_run.return_value = subprocess.CompletedProcess(
            args=["git", "status"], returncode=0, stdout="clean", stderr=""
        )

        safe_git_command(["status"])

        mock_safe_run.assert_called_once_with(
            ["git", "status"],
            timeout=None,
            check=True,
        )


class TestCommandAvailability:
    """Test command availability checking."""

    @patch("gh_actions_optimizer.shared.subprocess.safe_run")
    def test_check_command_availability_available(
        self, mock_safe_run: MagicMock
    ) -> None:
        """Test checking available command."""
        mock_safe_run.return_value = subprocess.CompletedProcess(
            args=["gh", "--version"], returncode=0, stdout="2.0.0", stderr=""
        )

        assert check_command_availability("gh") is True

    @patch("gh_actions_optimizer.shared.subprocess.safe_run")
    def test_check_command_availability_unavailable(
        self, mock_safe_run: MagicMock
    ) -> None:
        """Test checking unavailable command."""
        mock_safe_run.side_effect = FileNotFoundError()

        assert check_command_availability("nonexistent") is False

    @patch("gh_actions_optimizer.shared.subprocess.safe_run")
    def test_check_command_availability_error(self, mock_safe_run: MagicMock) -> None:
        """Test checking command that errors."""
        mock_safe_run.side_effect = subprocess.CalledProcessError(1, ["cmd"])

        assert check_command_availability("cmd") is False


class TestConstants:
    """Test module constants."""

    def test_allowed_commands_includes_required(self) -> None:
        """Test that all required commands are in allowed list."""
        required_commands = ["gh", "git", "jq"]
        for cmd in required_commands:
            assert cmd in ALLOWED_COMMANDS

    def test_default_timeout_reasonable(self) -> None:
        """Test that default timeout is reasonable."""
        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_TIMEOUT <= 300  # Not too long

    def test_max_arg_length_reasonable(self) -> None:
        """Test that max argument length is reasonable."""
        assert MAX_ARG_LENGTH > 0
        assert MAX_ARG_LENGTH >= 1024  # At least 1KB

    def test_sensitive_patterns_compiled(self) -> None:
        """Test that sensitive patterns are properly compiled."""
        assert len(SENSITIVE_PATTERNS) > 0
        for pattern in SENSITIVE_PATTERNS:
            assert hasattr(pattern, "search")  # Is compiled regex
