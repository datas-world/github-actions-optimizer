"""Safe subprocess execution utilities for GitHub Actions Optimizer.

This module provides secure subprocess execution patterns to prevent
command injection vulnerabilities and ensure safe interaction with
external commands like `gh` CLI and `git`.
"""

import re
import shlex
import subprocess
import time
from typing import Any, List, Optional, Pattern

from .cli import log_error, log_info, log_warn


# Patterns for detecting sensitive data that should not be logged
SENSITIVE_PATTERNS: List[Pattern[str]] = [
    re.compile(r"token[=:\s]+[a-zA-Z0-9_-]+", re.IGNORECASE),
    re.compile(r"gh[psu]_[a-zA-Z0-9_-]+", re.IGNORECASE),  # GitHub tokens
    re.compile(r"password[=:\s]+\S+", re.IGNORECASE),
    re.compile(r"secret[=:\s]+\S+", re.IGNORECASE),
    re.compile(r"key[=:\s]+[a-zA-Z0-9_/-]+", re.IGNORECASE),
]

# Allowed commands - whitelist approach for extra security
ALLOWED_COMMANDS: List[str] = [
    "gh",
    "git",
    "jq",
]

# Maximum argument length to prevent buffer overflow attempts
MAX_ARG_LENGTH = 4096

# Default timeout for subprocess calls (in seconds)
DEFAULT_TIMEOUT = 120


class SubprocessSecurityError(Exception):
    """Raised when a subprocess operation violates security constraints."""

    pass


def sanitize_for_logging(text: str) -> str:
    """Sanitize text to remove sensitive information before logging.

    Args:
        text: Text that may contain sensitive information

    Returns:
        Sanitized text safe for logging
    """
    if not text:
        return text

    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)

    return sanitized


def validate_command(command: str) -> None:
    """Validate that a command is in the allowed list.

    Args:
        command: Command name to validate

    Raises:
        SubprocessSecurityError: If command is not allowed
    """
    if not command:
        raise SubprocessSecurityError("Empty command not allowed")

    if command not in ALLOWED_COMMANDS:
        raise SubprocessSecurityError(
            f"Command '{command}' not in allowed list: {ALLOWED_COMMANDS}"
        )


def validate_arguments(args: List[str]) -> None:
    """Validate subprocess arguments for security.

    Args:
        args: List of arguments to validate

    Raises:
        SubprocessSecurityError: If arguments fail validation
    """
    if not args:
        raise SubprocessSecurityError("Empty argument list not allowed")

    # Validate command
    validate_command(args[0])

    # Check argument lengths
    for i, arg in enumerate(args):
        if not isinstance(arg, str):
            raise SubprocessSecurityError(
                f"Argument {i} must be a string, got {type(arg)}"
            )

        if len(arg) > MAX_ARG_LENGTH:
            raise SubprocessSecurityError(
                f"Argument {i} exceeds maximum length of {MAX_ARG_LENGTH}"
            )

    # Check for shell metacharacters in inappropriate contexts
    shell_chars = set(";|&$`(){}[]<>*?~")
    for i, arg in enumerate(args):
        if any(char in arg for char in shell_chars):
            # Allow certain shell chars in specific contexts (GitHub repos)
            if not _is_safe_shell_char_context(arg, i, args):
                log_warn(f"Argument {i} contains shell metacharacters: {arg}")


def _is_safe_shell_char_context(arg: str, index: int, args: List[str]) -> bool:
    """Check if shell characters are safe in the given context.

    Args:
        arg: Argument containing shell characters
        index: Index of argument in the list
        args: Full argument list for context

    Returns:
        True if shell characters are safe in this context
    """
    # Allow GitHub repository patterns like "owner/repo"
    if "/" in arg and re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", arg):
        return True

    # Allow GitHub API paths
    if index > 0 and args[0] == "gh" and "api" in args and "/" in arg:
        return True

    # Allow file extensions with dots
    if "." in arg and re.match(r"^[a-zA-Z0-9._/-]+$", arg):
        return True

    return False


def escape_argument(arg: str) -> str:
    """Escape a single argument for safe shell usage.

    Args:
        arg: Argument to escape

    Returns:
        Safely escaped argument
    """
    # Use shlex.quote for proper shell escaping
    return shlex.quote(arg)


def safe_run(
    args: List[str],
    *,
    timeout: Optional[int] = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    log_command: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Safely execute a subprocess with security validations.

    Args:
        args: Command arguments (first element must be the command)
        timeout: Maximum execution time in seconds
        check: Whether to raise on non-zero exit codes
        capture_output: Whether to capture stdout/stderr
        text: Whether to return text output (vs bytes)
        log_command: Whether to log the command being executed
        **kwargs: Additional arguments passed to subprocess.run

    Returns:
        CompletedProcess instance

    Raises:
        SubprocessSecurityError: If security validation fails
        subprocess.CalledProcessError: If check=True and process fails
        subprocess.TimeoutExpired: If timeout is exceeded
    """
    # Validate arguments
    validate_arguments(args)

    # Set default timeout
    if timeout is None:
        timeout = DEFAULT_TIMEOUT

    # Ensure shell=False for security
    kwargs["shell"] = False

    # Log command (with sanitization)
    if log_command:
        sanitized_args = [sanitize_for_logging(arg) for arg in args]
        log_info(f"Executing: {' '.join(sanitized_args)}")

    start_time = time.time()

    try:
        result = subprocess.run(
            args,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            text=text,
            **kwargs,
        )

        # Log execution time
        execution_time = time.time() - start_time
        log_info(f"Command completed in {execution_time:.2f}s")

        return result

    except subprocess.TimeoutExpired:
        log_error(f"Command timed out after {timeout}s: {args[0]}")
        raise

    except subprocess.CalledProcessError as e:
        # Sanitize error output before logging
        sanitized_stderr = sanitize_for_logging(e.stderr or "")
        log_error(f"Command failed with exit code {e.returncode}: {args[0]}")
        if sanitized_stderr:
            log_error(f"Error output: {sanitized_stderr}")
        raise


def safe_gh_command(
    gh_args: List[str],
    *,
    timeout: Optional[int] = None,
    check: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Safely execute a GitHub CLI command.

    Args:
        gh_args: Arguments to pass to gh CLI (without 'gh' prefix)
        timeout: Maximum execution time in seconds
        check: Whether to raise on non-zero exit codes
        **kwargs: Additional arguments passed to safe_run

    Returns:
        CompletedProcess instance

    Raises:
        SubprocessSecurityError: If security validation fails
        subprocess.CalledProcessError: If check=True and process fails
    """
    return safe_run(
        ["gh"] + gh_args,
        timeout=timeout,
        check=check,
        **kwargs,
    )


def safe_git_command(
    git_args: List[str],
    *,
    timeout: Optional[int] = None,
    check: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Safely execute a git command.

    Args:
        git_args: Arguments to pass to git (without 'git' prefix)
        timeout: Maximum execution time in seconds
        check: Whether to raise on non-zero exit codes
        **kwargs: Additional arguments passed to safe_run

    Returns:
        CompletedProcess instance

    Raises:
        SubprocessSecurityError: If security validation fails
        subprocess.CalledProcessError: If check=True and process fails
    """
    return safe_run(
        ["git"] + git_args,
        timeout=timeout,
        check=check,
        **kwargs,
    )


def check_command_availability(command: str) -> bool:
    """Check if a command is available on the system.

    Args:
        command: Command name to check

    Returns:
        True if command is available, False otherwise
    """
    try:
        safe_run(
            [command, "--version"],
            timeout=10,
            check=True,
            log_command=False,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        SubprocessSecurityError,
    ):
        return False
