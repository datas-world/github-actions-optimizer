"""Main entry point for GitHub Actions Optimizer."""

import argparse
import sys

from . import __description__, __name__, __version__
from .shared import add_common_args, add_output_args, check_dependencies, log_error


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all commands and options."""
    parser = argparse.ArgumentParser(
        prog=f"gh {__name__}",
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gh actions-optimizer analyze                 # Analyze current repository
  gh actions-optimizer analyze --sample-data  # Use sample data for testing
  gh actions-optimizer cost                    # Show runner costs
  gh actions-optimizer security               # Security audit
  gh actions-optimizer runners                # Runner optimization tips

For more information: https://github.com/datas-world/github-actions-optimizer
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"{__name__} {__version__}"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze workflows for optimization opportunities"
    )
    add_common_args(analyze_parser)
    analyze_parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Use sample data for testing (when repo access is limited)",
    )

    # Cost command
    cost_parser = subparsers.add_parser(
        "cost", help="Calculate and optimize workflow costs"
    )
    add_output_args(cost_parser)
    cost_parser.add_argument(
        "-w",
        "--web",
        action="store_true",
        help="Open GitHub Actions pricing in web browser",
    )

    # Security command
    security_parser = subparsers.add_parser(
        "security", help="Security audit of workflows and repository settings"
    )
    add_common_args(security_parser)
    security_parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Use sample data for testing (when repo access is limited)",
    )

    # Runners command
    runners_parser = subparsers.add_parser(
        "runners", help="Optimize runner usage and provide recommendations"
    )
    add_output_args(runners_parser)
    runners_parser.add_argument(
        "-w",
        "--web",
        action="store_true",
        help="Open GitHub Actions documentation in web browser",
    )

    # Generate subcommand group
    generate_parser = subparsers.add_parser(
        "generate", help="Generate configuration files and templates"
    )
    generate_subparsers = generate_parser.add_subparsers(
        dest="generate_command", help="Generate commands"
    )

    # Generate runner-setup
    runner_setup_parser = generate_subparsers.add_parser(
        "runner-setup", help="Generate optimal runner configuration"
    )
    add_common_args(runner_setup_parser)

    # Generate workflow-patch
    workflow_patch_parser = generate_subparsers.add_parser(
        "workflow-patch", help="Generate workflow optimization patches"
    )
    add_common_args(workflow_patch_parser)
    workflow_patch_parser.add_argument(
        "--workflow", help="Specific workflow file to patch"
    )

    # Validate subcommand group
    validate_parser = subparsers.add_parser(
        "validate", help="Validate configurations and setups"
    )
    validate_subparsers = validate_parser.add_subparsers(
        dest="validate_command", help="Validate commands"
    )

    # Validate runners
    validate_runners_parser = validate_subparsers.add_parser(
        "runners", help="Validate runner configurations"
    )
    add_common_args(validate_runners_parser)

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Benchmark and performance analysis"
    )
    add_common_args(benchmark_parser)
    benchmark_parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Analysis duration in days (default: 30)",
    )

    return parser


def main() -> None:
    """Execute the main entry point for the GitHub Actions optimizer."""
    check_dependencies()

    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # Route to appropriate command using pattern matching (Python 3.10+)
        match args.command:
            case "analyze":
                from .analyze import cmd_analyze
                cmd_analyze(args)
            case "cost":
                from .cost import cmd_cost
                cmd_cost(args)
            case "security":
                from .security import cmd_security
                cmd_security(args)
            case "runners":
                from .runners import cmd_runners
                cmd_runners(args)
            case "generate":
                if (
                    not hasattr(args, "generate_command")
                    or not args.generate_command
                ):
                    log_error(
                        "Generate subcommand required. Use --help for options."
                    )
                    sys.exit(1)

                match args.generate_command:
                    case "runner-setup":
                        from .generate.runner_setup import (
                            cmd_generate_runner_setup,
                        )
                        cmd_generate_runner_setup(args)
                    case "workflow-patch":
                        from .generate.workflow_patch import (
                            cmd_generate_workflow_patch,
                        )
                        cmd_generate_workflow_patch(args)
                    case _:
                        generate_cmd = args.generate_command
                        log_error(f"Unknown generate command: {generate_cmd}")
                        sys.exit(1)
            case "validate":
                if (
                    not hasattr(args, "validate_command")
                    or not args.validate_command
                ):
                    log_error(
                        "Validate subcommand required. Use --help for options."
                    )
                    sys.exit(1)

                match args.validate_command:
                    case "runners":
                        from .validate.runners import cmd_validate_runners
                        cmd_validate_runners(args)
                    case _:
                        validate_cmd = args.validate_command
                        log_error(f"Unknown validate command: {validate_cmd}")
                        sys.exit(1)
            case "benchmark":
                from .benchmark import cmd_benchmark
                cmd_benchmark(args)
            case _:
                log_error(f"Unknown command: {args.command}")
                sys.exit(1)
    except KeyboardInterrupt:
        from .shared import log_info
        log_info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        if hasattr(args, "verbose") and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
