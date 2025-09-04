"""Generate runner setup command implementation."""

import argparse
import json

from ...shared import Colors, log_info, log_success


def cmd_generate_runner_setup(args: argparse.Namespace) -> None:
    """Generate optimal runner configuration."""
    from ...shared.github import get_repo_for_command

    repo = get_repo_for_command(args)

    if not args.quiet:
        log_info(f"Generating optimal runner configuration for {repo}...")

    # Generate optimized runner setup
    runner_config = {
        "strategy": {
            "matrix": {
                "os": ["ubuntu-latest"],
                "python-version": ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"],
            }
        },
        "runs-on": "${{ matrix.os }}",
        "timeout-minutes": 10,
        "concurrency": {
            "group": "${{ github.workflow }}-${{ github.ref }}",
            "cancel-in-progress": True,
        },
        "steps": [
            {"name": "Checkout code", "uses": "actions/checkout@v4"},
            {
                "name": "Set up Python",
                "uses": "actions/setup-python@v5",
                "with": {"python-version": "${{ matrix.python-version }}"},
            },
            {
                "name": "Cache dependencies",
                "uses": "actions/cache@v4",
                "with": {
                    "path": "~/.cache/pip",
                    "key": (
                        "${{ runner.os }}-pip-"
                        "${{ hashFiles('**/requirements.txt') }}"
                    ),
                },
            },
        ],
    }

    if args.format == "json":
        if args.output:
            with open(args.output, "w") as f:
                json.dump(runner_config, f, indent=2)
            log_success(f"Runner configuration saved to {args.output}")
        else:
            print(json.dumps(runner_config, indent=2))
    else:
        print(f"\n{Colors.BOLD}Optimal Runner Configuration for {repo}{Colors.NC}")
        print("=" * 60)
        print("strategy:")
        print("  matrix:")
        print("    os: [ubuntu-latest]")
        print("    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']")
        print("runs-on: ${{ matrix.os }}")
        print("timeout-minutes: 10")
        print("concurrency:")
        print("  group: ${{ github.workflow }}-${{ github.ref }}")
        print("  cancel-in-progress: true")
