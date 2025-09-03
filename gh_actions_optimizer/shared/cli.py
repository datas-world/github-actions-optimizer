"""CLI utilities for GitHub Actions Optimizer."""

import argparse
import sys
from typing import Any, Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output formatting."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    BOLD = "\033[1m"
    NC = "\033[0m"  # No Color


def log_info(message: str) -> None:
    """Log info message to stderr."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}", file=sys.stderr)


def log_warn(message: str) -> None:
    """Log warning message to stderr."""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}", file=sys.stderr)


def log_error(message: str) -> None:
    """Log error message to stderr."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)


def log_success(message: str) -> None:
    """Log success message to stderr."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}", file=sys.stderr)


def add_common_args(parser_obj: argparse.ArgumentParser, repo_required: bool = False) -> None:
    """Add common arguments to a parser."""
    parser_obj.add_argument(
        "-R",
        "--repo",
        required=repo_required,
        help="Select another repository using the [HOST/]OWNER/REPO format",
    )
    parser_obj.add_argument(
        "-f",
        "--format",
        choices=["table", "json", "yaml"],
        default="table",
        help="Output format (default: table)",
    )
    parser_obj.add_argument(
        "-o", "--output", help="Output file (default: stdout)")
    parser_obj.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    parser_obj.add_argument(
        "-q", "--quiet", action="store_true", help="Minimal output"
    )
    parser_obj.add_argument(
        "-w", "--web", action="store_true", help="Open results in web browser"
    )


def add_output_args(parser_obj: argparse.ArgumentParser) -> None:
    """Add output-only arguments."""
    parser_obj.add_argument(
        "-f",
        "--format",
        choices=["table", "json", "yaml"],
        default="table",
        help="Output format (default: table)",
    )
    parser_obj.add_argument(
        "-o", "--output", help="Output file (default: stdout)")
    parser_obj.add_argument(
        "-q", "--quiet", action="store_true", help="Minimal output"
    )


def check_dependencies() -> None:
    """Check if required dependencies are available."""
    import subprocess  # nosec B404

    deps = ["gh", "jq"]
    missing = []

    for dep in deps:
        try:
            subprocess.run([dep, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(dep)

    if missing:
        log_error(f"Missing required dependencies: {', '.join(missing)}")
        log_info("Please install the missing dependencies and try again.")
        sys.exit(1)
