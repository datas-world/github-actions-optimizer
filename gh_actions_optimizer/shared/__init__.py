"""Shared utilities for GitHub Actions Optimizer."""

from .cli import (
    Colors,
    add_common_args,
    add_output_args,
    check_dependencies,
    colors,
    log_error,
    log_info,
    log_success,
    log_warn,
    validate_parsed_args,
)
from .data import get_sample_security_data, get_sample_workflows
from .github import (
    download_workflow_content,
    get_current_repo,
    get_repo_for_command,
    get_workflows,
    run_gh_command,
    validate_repo,
)
from .output import (
    format_output,
    format_table,
    open_github_docs,
    open_github_pricing,
    open_in_browser,
)
from .validation import (
    InputValidator,
    ValidationError,
    validate_and_log_error,
)

__all__ = [
    # CLI utilities
    "Colors",
    "add_common_args",
    "add_output_args",
    "check_dependencies",
    "colors",
    "log_error",
    "log_info",
    "log_success",
    "log_warn",
    "validate_parsed_args",
    # Data utilities
    "get_sample_security_data",
    "get_sample_workflows",
    # GitHub utilities
    "download_workflow_content",
    "get_current_repo",
    "get_repo_for_command",
    "get_workflows",
    "run_gh_command",
    "validate_repo",
    # Output utilities
    "format_output",
    "format_table",
    "open_github_docs",
    "open_github_pricing",
    "open_in_browser",
    # Validation utilities
    "InputValidator",
    "ValidationError",
    "validate_and_log_error",
]
