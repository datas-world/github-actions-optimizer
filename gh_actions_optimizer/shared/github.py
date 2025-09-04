"""GitHub API and repository utilities."""

import argparse
import json
import os
import sys
import urllib.request
from typing import Any, Dict, List, Optional, cast

from .cli import log_error, log_info
from .subprocess import safe_gh_command, safe_git_command


def get_current_repo() -> Optional[str]:
    """Get current repository from gh CLI, GitHub Actions env vars, or git remote."""
    # First try GitHub Actions environment variables
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    if github_repository:
        log_info(f"Using GitHub Actions repository: {github_repository}")
        return github_repository

    try:
        # Try gh CLI second
        result = safe_gh_command(
            ["repo", "view", "--json", "nameWithOwner"],
            timeout=30,
        )
        repo_info = json.loads(result.stdout)
        repo_raw = repo_info.get("nameWithOwner")
        if repo_raw and isinstance(repo_raw, str):
            log_info(f"Using gh CLI detected repository: {repo_raw}")
            return cast(str, repo_raw)
    except Exception:
        # Catch all exceptions including our security errors
        pass

    try:
        # Fallback to git remote
        result = safe_git_command(
            ["remote", "get-url", "origin"],
            timeout=15,
        )
        remote_url = result.stdout.strip()
        # Parse GitHub URL to get owner/repo
        if "github.com" in remote_url:
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            parts = remote_url.split("/")[-2:]
            if len(parts) == 2:
                repo = f"{parts[0]}/{parts[1]}"
                log_info(f"Using git remote detected repository: {repo}")
                return repo
    except Exception:
        # Catch all exceptions including our security errors
        pass

    return None


def validate_repo(repo: Optional[str]) -> str:
    """Validate repository format or get current repo."""
    if not repo:
        repo = get_current_repo()
        if not repo:
            log_error(
                "No repository specified and unable to detect current " "repository"
            )
            log_info("Use --repo owner/repo or run from within a GitHub repository")
            log_info("Or use --sample-data to test with sample data")
            sys.exit(1)
        log_info(f"Using current repository: {repo}")

    if "/" not in repo:
        log_error("Invalid repository format. Expected: owner/repo")
        sys.exit(1)

    parts = repo.split("/")
    if len(parts) != 2 or not all(part.strip() for part in parts):
        log_error("Invalid repository format. Expected: owner/repo")
        sys.exit(1)

    return repo


def get_repo_for_command(args: argparse.Namespace) -> str:
    """Get repository for command, handling sample data case."""
    if hasattr(args, "sample_data") and args.sample_data:
        return "sample/repo"

    # Check if repo was provided via command line
    repo = getattr(args, "repo", None)

    # If no repo specified, try to auto-detect
    if not repo:
        repo = get_current_repo()
        if not repo:
            log_error(
                "No repository specified and unable to detect current " "repository"
            )
            log_info("Use --repo owner/repo, run from within a GitHub repository,")
            log_info("or use --sample-data to test with sample data")
            sys.exit(1)

    return validate_repo(repo)


def run_gh_command(
    args: List[str], check: bool = True
) -> Any:  # Using Any temporarily for backward compatibility
    """Run a gh CLI command.

    This function is deprecated. Use safe_gh_command instead.
    """
    log_info("Using legacy run_gh_command. Consider upgrading to safe_gh_command.")
    try:
        return safe_gh_command(args, check=check)
    except Exception as e:
        log_error(f"GitHub CLI command failed: {e}")
        if hasattr(e, "stderr") and e.stderr:
            log_error(f"Error output: {e.stderr}")
        sys.exit(1)


def get_workflows(repo: str) -> List[Dict[str, Any]]:
    """Get workflow files from repository."""
    log_info(f"Fetching workflows from {repo}...")

    result = safe_gh_command(
        [
            "api",
            f"repos/{repo}/contents/.github/workflows",
            "--jq",
            '.[] | select(.type == "file" and '
            '(.name | endswith(".yml") or endswith(".yaml")))',
        ],
        check=False,
        timeout=60,
    )

    if result.returncode != 0:
        log_error(
            "Failed to fetch workflows. Check repository access and " "permissions."
        )
        return []

    workflows = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            try:
                workflow = json.loads(line)
                workflows.append(workflow)
            except json.JSONDecodeError:
                continue

    return workflows


def download_workflow_content(download_url: str) -> str:
    """Download workflow content from URL."""
    try:
        with urllib.request.urlopen(download_url) as response:  # nosec B310
            content_bytes = cast(bytes, response.read())
            content = content_bytes.decode("utf-8")
            return content
    except (urllib.error.URLError, UnicodeDecodeError) as e:
        log_error(f"Failed to download workflow content: {e}")
        return ""
