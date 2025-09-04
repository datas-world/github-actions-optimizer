"""GitHub API and repository utilities."""

import argparse
import json
import os
import subprocess  # nosec B404
import sys
import urllib.request
from typing import Any, Dict, List, Optional, cast

from .cli import log_error, log_info
from .validation import InputValidator, ValidationError, validate_and_log_error


def get_current_repo() -> Optional[str]:
    """Get current repository from gh CLI, GitHub Actions env vars, or git remote."""
    # First try GitHub Actions environment variables
    github_repository = os.environ.get("GITHUB_REPOSITORY")
    if github_repository:
        # Validate the environment variable value for security
        try:
            validated_repo = InputValidator.validate_repository_name(github_repository)
            log_info(f"Using GitHub Actions repository: {validated_repo}")
            return validated_repo
        except ValidationError:
            # If env var is invalid, fall through to other detection methods
            pass

    try:
        # Try gh CLI second
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,  # Add timeout for safety
            env={
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME", ""),
            },  # Minimal environment
        )
        repo_info = json.loads(result.stdout)
        repo_raw = repo_info.get("nameWithOwner")
        if repo_raw and isinstance(repo_raw, str):
            # Validate the repository name for security
            validated_repo = InputValidator.validate_repository_name(repo_raw)
            log_info(f"Using gh CLI detected repository: {validated_repo}")
            return validated_repo
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
        FileNotFoundError,
        ValidationError,
    ):
        pass

    try:
        # Fallback to git remote
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,  # Add timeout for safety
            env={"PATH": os.environ.get("PATH", "")},  # Minimal environment
        )
        remote_url = result.stdout.strip()
        
        # Validate URL format first
        if not remote_url or len(remote_url) > 2048:  # Reasonable URL length limit
            return None
            
        # Parse GitHub URL to get owner/repo
        if "github.com" in remote_url:
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            parts = remote_url.split("/")[-2:]
            if len(parts) == 2 and parts[0] and parts[1]:  # Ensure both parts exist and are non-empty
                repo = f"{parts[0]}/{parts[1]}"
                # Validate the repository name for security
                try:
                    validated_repo = InputValidator.validate_repository_name(repo)
                    log_info(f"Using git remote detected repository: {validated_repo}")
                    return validated_repo
                except ValidationError:
                    # If validation fails, don't return the repo
                    pass
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValidationError):
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

    # Use comprehensive validation
    validated_repo = validate_and_log_error(InputValidator.validate_repository_name, repo)
    return cast(str, validated_repo)


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
    """Run a gh CLI command with enhanced security."""
    import shutil
    
    # Validate all arguments for security
    for arg in args:
        if not isinstance(arg, str):
            log_error("Invalid argument type for GitHub CLI command")
            sys.exit(1)
        validate_and_log_error(InputValidator.sanitize_for_shell, arg)
    
    try:
        # Ensure gh CLI is available and get its path
        gh_path = shutil.which("gh")
        if not gh_path:
            log_error("GitHub CLI (gh) not found in PATH")
            sys.exit(1)
            
        result = subprocess.run(
            [gh_path] + args, 
            capture_output=True, 
            text=True, 
            check=check,
            timeout=30,  # Add timeout for safety
            env={
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME", ""),
            },  # Minimal environment
        )
        return result
    except subprocess.TimeoutExpired:
        log_error("GitHub CLI command timed out")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        log_error(f"GitHub CLI command failed: {e}")
        if e.stderr:
            log_error(f"Error output: {e.stderr}")
        sys.exit(1)


def get_workflows(repo: str) -> List[Dict[str, Any]]:
    """Get workflow files from repository."""
    log_info(f"Fetching workflows from {repo}...")

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
    """Download workflow content from URL with enhanced security."""
    # Validate URL
    validated_url = validate_and_log_error(
        InputValidator.validate_url, 
        download_url, 
        ["https"]  # Only allow HTTPS for security
    )
    
    # Additional security checks for GitHub URLs
    if "github.com" not in validated_url and "githubusercontent.com" not in validated_url:
        log_error("URL must be from GitHub or GitHub user content domains")
        return ""
    
    try:
        import ssl
        # Create secure SSL context
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        request = urllib.request.Request(
            validated_url,
            headers={
                "User-Agent": "github-actions-optimizer/1.0",
                "Accept": "text/plain, application/x-yaml, text/yaml",
            }
        )
        
        with urllib.request.urlopen(request, context=context, timeout=30) as response:  # nosec B310
            # Check content type
            content_type = response.headers.get("Content-Type", "")
            if content_type and not any(ct in content_type.lower() for ct in ["text/", "yaml", "yml"]):
                log_error(f"Invalid content type: {content_type}")
                return ""
                
            content_bytes = cast(bytes, response.read())
            content = content_bytes.decode("utf-8")
            
            # Validate content size
            validate_and_log_error(
                InputValidator.validate_input_length,
                content,
                InputValidator.MAX_CONTENT_LENGTH,
                "Workflow content"
            )
            
            return content
    except (urllib.error.URLError, UnicodeDecodeError, ssl.SSLError) as e:
        log_error(f"Failed to download workflow content: {e}")
        return ""
