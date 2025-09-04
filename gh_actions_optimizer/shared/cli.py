"""CLI utilities for GitHub Actions Optimizer."""

import argparse
import os
import sys
from typing import TextIO

from rich.console import Console

from .validation import InputValidator, validate_and_log_error


class Colors:
    """Intelligent color handling with automatic terminal capability detection."""

    def __init__(self) -> None:
        """Initialize Colors with Rich-based terminal detection."""
        # Create console instances for different output streams
        self._console_stdout = Console(
            file=sys.stdout,
            force_terminal=self._should_force_color(),
            no_color=self._should_disable_color(),
            color_system="auto",  # Let Rich auto-detect capabilities
        )

        self._console_stderr = Console(
            file=sys.stderr,
            force_terminal=self._should_force_color(),
            no_color=self._should_disable_color(),
            color_system="auto",  # Let Rich auto-detect capabilities
        )

    def _should_force_color(self) -> bool:
        """Check if color output should be forced."""
        force_color = os.environ.get("FORCE_COLOR", "")
        # Enhanced sanitization for safety
        try:
            validated_env = InputValidator.validate_environment_variable("FORCE_COLOR", force_color)
            force_color = validated_env[1]
        except Exception:
            # If validation fails, fall back to safe default
            force_color = ""
        return force_color in ("1", "true", "True", "TRUE")

    def _should_disable_color(self) -> bool:
        """Check if color output should be disabled."""
        no_color = os.environ.get("NO_COLOR", "")
        force_color = os.environ.get("FORCE_COLOR", "")
        
        # Enhanced sanitization for safety
        try:
            if no_color:
                validated = InputValidator.validate_environment_variable("NO_COLOR", no_color)
                no_color = validated[1]
        except Exception:
            no_color = ""
            
        try:
            if force_color:
                validated = InputValidator.validate_environment_variable("FORCE_COLOR", force_color)
                force_color = validated[1]
        except Exception:
            force_color = ""

        # FORCE_COLOR=0 explicitly disables color
        if force_color == "0":
            return True
        # NO_COLOR disables color unless FORCE_COLOR=1 is explicitly set
        if no_color and force_color != "1":
            return True
        # Also check if not a TTY and no explicit force
        if not sys.stderr.isatty() and force_color not in ("1", "true", "True", "TRUE"):
            return True
        return False

    def get_console(self, file: TextIO = sys.stderr) -> Console:
        """Get appropriate Console instance for the given file stream."""
        if file == sys.stdout:
            return self._console_stdout
        return self._console_stderr

    # Compatibility methods for existing code
    def red(self, text: str) -> str:
        """Get red-colored text if terminal supports it."""
        if self._should_disable_color():
            return text
        return f"[red]{text}[/red]"

    def green(self, text: str) -> str:
        """Get green-colored text if terminal supports it."""
        if self._should_disable_color():
            return text
        return f"[green]{text}[/green]"

    def yellow(self, text: str) -> str:
        """Get yellow-colored text if terminal supports it."""
        if self._should_disable_color():
            return text
        return f"[yellow]{text}[/yellow]"

    def blue(self, text: str) -> str:
        """Get blue-colored text if terminal supports it."""
        if self._should_disable_color():
            return text
        return f"[blue]{text}[/blue]"

    def bold(self, text: str) -> str:
        """Get bold text if terminal supports it."""
        if self._should_disable_color():
            return text
        return f"[bold]{text}[/bold]"

    # Legacy ANSI-style properties for backward compatibility
    @property
    def RED(self) -> str:
        """Legacy red color code."""
        return "" if self._should_disable_color() else "\033[0;31m"

    @property
    def GREEN(self) -> str:
        """Legacy green color code."""
        return "" if self._should_disable_color() else "\033[0;32m"

    @property
    def YELLOW(self) -> str:
        """Legacy yellow color code."""
        return "" if self._should_disable_color() else "\033[1;33m"

    @property
    def BLUE(self) -> str:
        """Legacy blue color code."""
        return "" if self._should_disable_color() else "\033[0;34m"

    @property
    def BOLD(self) -> str:
        """Legacy bold code."""
        return "" if self._should_disable_color() else "\033[1m"

    @property
    def NC(self) -> str:
        """Legacy reset code."""
        return "" if self._should_disable_color() else "\033[0m"


# Create a singleton instance for backward compatibility
colors = Colors()


def log_info(message: str) -> None:
    """Log info message to stderr using Rich console."""
    console = colors.get_console(sys.stderr)
    console.print(f"[blue][INFO][/blue] {message}", highlight=False)


def log_warn(message: str) -> None:
    """Log warning message to stderr using Rich console."""
    console = colors.get_console(sys.stderr)
    console.print(f"[yellow][WARN][/yellow] {message}", highlight=False)


def log_error(message: str) -> None:
    """Log error message to stderr using Rich console."""
    console = colors.get_console(sys.stderr)
    console.print(f"[red][ERROR][/red] {message}", highlight=False)


def log_success(message: str) -> None:
    """Log success message to stderr using Rich console."""
    console = colors.get_console(sys.stderr)
    console.print(f"[green][SUCCESS][/green] {message}", highlight=False)


def add_common_args(
    parser_obj: argparse.ArgumentParser, repo_required: bool = False
) -> None:
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
    parser_obj.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser_obj.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    parser_obj.add_argument("-q", "--quiet", action="store_true", help="Minimal output")
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
    parser_obj.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser_obj.add_argument("-q", "--quiet", action="store_true", help="Minimal output")


def check_dependencies() -> None:
    """Check if required dependencies are available."""
    import subprocess  # nosec B404
    import shutil

    deps = ["gh", "jq"]
    missing = []

    for dep in deps:
        try:
            # Use shutil.which for safer path resolution
            if not shutil.which(dep):
                missing.append(dep)
                continue
                
            # Validate dependency name for security
            validate_and_log_error(InputValidator.sanitize_for_shell, dep)
            
            # Use explicit path and minimal arguments
            result = subprocess.run(
                [shutil.which(dep), "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,  # Add timeout for safety
                env={"PATH": os.environ.get("PATH", "")},  # Minimal environment
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            missing.append(dep)

    if missing:
        log_error(f"Missing required dependencies: {', '.join(missing)}")
        log_info("Please install the missing dependencies and try again.")
        sys.exit(1)


def validate_parsed_args(args: argparse.Namespace) -> None:
    """Validate parsed command-line arguments for security."""
    # Validate repository if provided
    if hasattr(args, "repo") and args.repo:
        validate_and_log_error(InputValidator.validate_repository_name, args.repo)
    
    # Validate output file path if provided
    if hasattr(args, "output") and args.output:
        validate_and_log_error(InputValidator.validate_file_path, args.output, True)
        validate_and_log_error(InputValidator.validate_filename, 
                             os.path.basename(args.output))
    
    # Validate workflow file path if provided (for workflow-patch command)
    if hasattr(args, "workflow") and args.workflow:
        validate_and_log_error(InputValidator.validate_file_path, args.workflow, True)
        validate_and_log_error(InputValidator.validate_file_extension,
                             args.workflow, [".yml", ".yaml"])
    
    # Validate format argument
    if hasattr(args, "format") and args.format:
        if args.format not in ["table", "json", "yaml"]:
            log_error(f"Invalid format: {args.format}")
            sys.exit(1)
    
    # Validate duration for benchmark command
    if hasattr(args, "duration") and args.duration is not None:
        if not isinstance(args.duration, int) or args.duration < 1 or args.duration > 365:
            log_error("Duration must be between 1 and 365 days")
            sys.exit(1)
