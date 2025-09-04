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
)
from .config import (
    get_github_token,
    secure_config,
    validate_configuration,
)
from .data import get_sample_security_data, get_sample_workflows
from .github import (
    download_workflow_content,
    get_current_repo,
    get_github_token_scopes,
    get_repo_for_command,
    get_workflows,
    run_gh_command,
    validate_github_auth,
    validate_repo,
)
from .output import (
    format_output,
    format_table,
    open_github_docs,
    open_github_pricing,
    open_in_browser,
)
from .security import (
    mask_repository_url,
    sanitize_error_message,
    sanitize_for_logging,
    sanitize_subprocess_output,
    validate_github_token_format,
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
    # Configuration utilities
    "get_github_token",
    "secure_config", 
    "validate_configuration",
    # Data utilities
    "get_sample_security_data",
    "get_sample_workflows",
    # GitHub utilities
    "download_workflow_content",
    "get_current_repo",
    "get_github_token_scopes", 
    "get_repo_for_command",
    "get_workflows",
    "run_gh_command",
    "validate_github_auth",
    "validate_repo",
    "get_workflows",
    "run_gh_command",
    "validate_repo",
    # Output utilities
    "format_output",
    "format_table",
    "open_github_docs",
    "open_github_pricing",
    "open_in_browser",
    # Security utilities
    "mask_repository_url",
    "sanitize_error_message", 
    "sanitize_for_logging",
    "sanitize_subprocess_output",
    "validate_github_token_format",
]
