"""Cost command implementation."""

import argparse

from ..shared import (
    Colors,
    format_output,
    log_info,
    log_success,
    open_github_pricing,
)
from .calculator import get_optimization_tips, get_runner_costs


def cmd_cost(args: argparse.Namespace) -> None:
    """Calculate and display workflow costs."""
    if not args.quiet:
        log_info("Calculating workflow costs...")

    costs = get_runner_costs()
    tips = get_optimization_tips()

    output_data = {
        "runner_costs_per_minute": costs,
        "currency": "USD",
        "last_updated": "2025-09-03",
        "optimization_tips": tips,
    }

    # Handle different output formats
    if args.format in ["json", "yaml"]:
        format_output(output_data, args.format, args.output)
        if args.output:
            log_success(f"Cost analysis saved to {args.output}")
    else:
        # Table format with custom formatting
        _format_cost_table(costs, tips, args)

    if args.web:
        open_github_pricing()


def _format_cost_table(
    costs: dict, tips: list, args: argparse.Namespace
) -> None:
    """Format cost data as a table."""
    output_lines = []

    if not args.quiet:
        header = (
            f"{Colors.BOLD}GitHub Actions Runner Costs "
            f"(per minute){Colors.NC}"
        )
        separator = "=" * 50
        output_lines.extend([header, separator, ""])

    for runner, cost in costs.items():
        output_lines.append(f"  {runner:<20} ${cost:.3f}")

    if not args.quiet:
        tips_header = f"\n{Colors.BLUE}Cost Optimization Tips:{Colors.NC}"
        output_lines.append(tips_header)
        for tip in tips:
            output_lines.append(f"  - {tip}")

    # Output to console or file
    output_text = "\n".join(output_lines)

    if args.output:
        # Save clean version without ANSI codes for file
        clean_lines = []
        clean_lines.append("GitHub Actions Runner Costs (per minute)")
        clean_lines.append("=" * 50)
        clean_lines.append("")

        for runner, cost in costs.items():
            clean_lines.append(f"  {runner:<20} ${cost:.3f}")

        clean_lines.append("\nCost Optimization Tips:")
        for tip in tips:
            clean_lines.append(f"  - {tip}")

        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("\n".join(clean_lines))
            log_success(f"Cost analysis saved to {args.output}")
        except OSError as e:
            log_info(f"Failed to write output file: {e}")
    else:
        print(output_text)
