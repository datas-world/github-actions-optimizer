"""Analyze command implementation."""

import argparse
import json
import sys
from typing import Any, Dict, List

import yaml

from ..shared import (
    Colors,
    download_workflow_content,
    format_output,
    get_repo_for_command,
    get_sample_workflows,
    get_workflows,
    log_info,
    log_success,
    log_warn,
)
from .workflow import analyze_workflow


def cmd_analyze(args: argparse.Namespace) -> None:
    """Analyze workflows for optimization opportunities."""
    repo = get_repo_for_command(args)

    if args.sample_data:
        if not args.quiet:
            log_info("Using sample data for analysis...")
        workflows = get_sample_workflows()
    else:
        workflows = get_workflows(repo)

    if not workflows:
        log_info(f"No workflows found in {repo}")
        return

    results = []

    for workflow in workflows:
        name = workflow.get("name", "unknown")

        if args.sample_data:
            content = workflow.get("content", "")
        else:
            download_url = workflow.get("download_url")
            if not download_url:
                log_warn(f"No download URL for workflow: {name}")
                continue

            if args.verbose:
                log_info(f"Downloading workflow: {name}")
            content = download_workflow_content(download_url)

        if content:
            analysis = analyze_workflow(content, name)
            results.append(analysis)

    # Prepare output data
    output_data = {"repository": repo, "workflows": results}

    # Handle different output formats
    if args.format in ["json", "yaml"]:
        format_output(output_data, args.format, args.output)
    else:
        # Table format with custom formatting
        _format_analyze_table(results, repo, args)


def _format_analyze_table(
    results: List[Dict[str, Any]], repo: str, args: argparse.Namespace
) -> None:
    """Format analysis results as a table."""
    output_lines = []

    if not args.quiet:
        header = f"{Colors.BOLD}Analysis Results for {repo}{Colors.NC}"
        separator = "=" * 60
        output_lines.extend([header, separator])

    for result in results:
        workflow_header = f"{Colors.BOLD}Workflow: {result['name']}{Colors.NC}"
        output_lines.append(f"\n{workflow_header}")

        if result["has_issues"]:
            issues_header = f"{Colors.YELLOW}Issues found:{Colors.NC}"
            output_lines.append(issues_header)
            for issue in result["issues"]:
                output_lines.append(f"  - {issue}")

            recs_header = f"{Colors.BLUE}Recommendations:{Colors.NC}"
            output_lines.append(recs_header)
            for rec in result["recommendations"]:
                output_lines.append(f"  - {rec}")
        else:
            no_issues = f"{Colors.GREEN}No optimization issues found{Colors.NC}"
            output_lines.append(no_issues)

    # Output to console or file
    output_text = "\n".join(output_lines)

    if args.output:
        # Save clean version without ANSI codes for file
        clean_lines = []
        clean_lines.append(f"Analysis Results for {repo}")
        clean_lines.append("=" * 60)

        for result in results:
            clean_lines.append(f"\nWorkflow: {result['name']}")
            if result["has_issues"]:
                clean_lines.append("Issues found:")
                for issue in result["issues"]:
                    clean_lines.append(f"  - {issue}")
                clean_lines.append("Recommendations:")
                for rec in result["recommendations"]:
                    clean_lines.append(f"  - {rec}")
            else:
                clean_lines.append("No optimization issues found")

        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("\n".join(clean_lines))
            log_success(f"Analysis saved to {args.output}")
        except OSError as e:
            log_warn(f"Failed to write output file: {e}")
    else:
        print(output_text)
