"""GitHub API and repository utilities."""

import argparse
import json
import os
import subprocess  # nosec B404
import sys
import urllib.request
from typing import Any, Dict, List, Optional, cast

from .cli import log_error, log_info


def get_current_repo() -> Optional[str]:
    """Get current repository from gh CLI, GitHub Actions env vars, or git remote."""
    from .security import mask_repository_url
    
    # First try GitHub Actions environment variables
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    if github_repository:
        # Only log the repo name, not any embedded credentials
        safe_repo = mask_repository_url(github_repository)
        log_info(f"Using GitHub Actions repository: {safe_repo}")
        return github_repository

    try:
        # Try gh CLI second
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_info = json.loads(result.stdout)
        repo_raw = repo_info.get("nameWithOwner")
        if repo_raw and isinstance(repo_raw, str):
            safe_repo = mask_repository_url(repo_raw)
            log_info(f"Using gh CLI detected repository: {safe_repo}")
            return cast(str, repo_raw)
    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        FileNotFoundError,
    ):
        pass

    try:
        # Fallback to git remote
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()
        # Parse GitHub URL to get owner/repo
        if "github.com" in remote_url:
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            parts = remote_url.split("/")[-2:]
            if len(parts) == 2:
                repo = f"{parts[0]}/{parts[1]}"
                # Mask any credentials in the URL before logging
                safe_repo = mask_repository_url(repo)
                log_info(f"Using git remote detected repository: {safe_repo}")
                return repo
    except subprocess.CalledProcessError:
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
) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command with secure error handling."""
    from .security import sanitize_subprocess_output
    
    try:
        result = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"GitHub CLI command failed: {e}")
        if e.stderr:
            # Sanitize error output to prevent token/credential exposure
            safe_stderr = sanitize_subprocess_output(e.stderr, ["gh"] + args)
            log_error(f"Error output: {safe_stderr}")
        sys.exit(1)


def get_workflows(repo: str) -> List[Dict[str, Any]]:
    """Get workflow files from repository."""
    from .security import mask_repository_url
    
    safe_repo = mask_repository_url(repo)
    log_info(f"Fetching workflows from {safe_repo}...")

    result = run_gh_command(
        [
            "api",
            f"repos/{repo}/contents/.github/workflows",
            "--jq",
            '.[] | select(.type == "file" and '
            '(.name | endswith(".yml") or endswith(".yaml")))',
        ],
        check=False,
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
    """Download workflow content from URL with secure error handling."""
    from .security import mask_repository_url, sanitize_error_message
    
    try:
        with urllib.request.urlopen(download_url) as response:  # nosec B310
            content_bytes = cast(bytes, response.read())
            content = content_bytes.decode("utf-8")
            return content
    except (urllib.error.URLError, UnicodeDecodeError) as e:
        # Sanitize URL and error message before logging
        safe_url = mask_repository_url(download_url)
        safe_error = sanitize_error_message(str(e))
        log_error(f"Failed to download workflow content from {safe_url}: {safe_error}")
        return ""


def validate_github_auth() -> bool:
    """Validate GitHub authentication without exposing tokens."""
    from .security import validate_github_token_format
    
    try:
        # Check if gh CLI is authenticated
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            log_info("GitHub authentication validated successfully")
            return True
        else:
            log_error("GitHub authentication failed. Run 'gh auth login' to authenticate.")
            return False
            
    except subprocess.CalledProcessError:
        log_error("Failed to check GitHub authentication status")
        return False
    except FileNotFoundError:
        log_error("GitHub CLI (gh) not found. Please install it first.")
        return False


def get_github_token_scopes() -> List[str]:
    """Get GitHub token scopes without exposing the token."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        if result.stdout.strip():
            # Don't log the actual token, just verify we have one
            log_info("GitHub token retrieved successfully")
            
            # Get token scopes using a separate API call
            scope_result = subprocess.run(
                ["gh", "api", "/user", "--include", "x-oauth-scopes"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            if scope_result.returncode == 0:
                # Extract scopes from headers (this is safe to log)
                headers = scope_result.stderr
                if "x-oauth-scopes:" in headers:
                    scopes_line = [line for line in headers.split("\n") if "x-oauth-scopes:" in line][0]
                    scopes = scopes_line.split(":")[1].strip().split(", ") if scopes_line.split(":")[1].strip() else []
                    log_info(f"GitHub token scopes: {', '.join(scopes) if scopes else 'none'}")
                    return scopes
            
            return []
            
    except subprocess.CalledProcessError:
        log_error("Failed to retrieve GitHub token information")
        return []
    except FileNotFoundError:
        log_error("GitHub CLI (gh) not found")
        return []
