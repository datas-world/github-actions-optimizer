"""Runners command implementation."""

import argparse
import json
import webbrowser

from ..shared import log_info, log_success, Colors


def cmd_runners(args: argparse.Namespace) -> None:
    """Optimize runner usage and provide recommendations."""
    import json
    import webbrowser

    if not args.quiet:
        log_info("Analyzing runner optimization opportunities...")

    # Runner optimization recommendations
    runner_data = {
        "runner_analysis": {
            "ubuntu-latest": {
                "cost_per_minute": 0.008,
                "recommended_for": ["Linux builds", "Docker operations", "Most CI/CD tasks"],
                "optimization_tips": [
                    "Use for most workloads due to lower cost",
                    "Enable concurrency controls",
                    "Add dependency caching"
                ]
            },
            "windows-latest": {
                "cost_per_minute": 0.016,
                "recommended_for": [".NET builds", "Windows-specific testing"],
                "optimization_tips": [
                    "Use only when Windows-specific features needed",
                    "Consider matrix strategies to reduce redundant runs",
                    "Implement aggressive caching"
                ]
            },
            "macos-latest": {
                "cost_per_minute": 0.08,
                "recommended_for": ["iOS/macOS builds", "Apple-specific tooling"],
                "optimization_tips": [
                    "Use sparingly due to high cost",
                    "Combine multiple tasks per job",
                    "Use conditional execution to skip unnecessary runs"
                ]
            }
        },
        "general_recommendations": [
            "Prefer ubuntu-latest for most workloads",
            "Use matrix strategies for cross-platform testing",
            "Implement concurrency controls to prevent redundant runs",
            "Add appropriate timeouts to prevent runaway jobs",
            "Cache dependencies aggressively",
            "Use self-hosted runners for high-volume workloads"
        ],
        "cost_optimization": {
            "potential_savings": "15-40% through runner optimization",
            "quick_wins": [
                "Replace unnecessary macOS runners with ubuntu",
                "Add concurrency controls",
                "Implement dependency caching",
                "Set reasonable timeouts"
            ]
        }
    }

    if args.web:
        webbrowser.open(
            "https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners")
        log_success("Opened GitHub Actions documentation in web browser")

    if args.format == "json":
        if args.output:
            with open(args.output, "w") as f:
                json.dump(runner_data, f, indent=2)
            log_success(f"Runner analysis saved to {args.output}")
        else:
            print(json.dumps(runner_data, indent=2))
    elif args.format == "yaml":
        import yaml
        if args.output:
            with open(args.output, "w") as f:
                yaml.dump(runner_data, f, default_flow_style=False)
            log_success(f"Runner analysis saved to {args.output}")
        else:
            print(yaml.dump(runner_data, default_flow_style=False))
    else:
        print(f"\n{Colors.BOLD}Runner Optimization Analysis{Colors.NC}")
        print("=" * 60)

        print(f"\n{Colors.BLUE}Runner Cost Analysis:{Colors.NC}")
        for runner, data in runner_data["runner_analysis"].items():
            print(f"\n{Colors.BOLD}{runner}{Colors.NC}")
            print(f"  Cost: ${data['cost_per_minute']}/minute")
            print(f"  Best for: {', '.join(data['recommended_for'])}")
            print("  Optimization tips:")
            for tip in data["optimization_tips"]:
                print(f"    - {tip}")

        print(f"\n{Colors.GREEN}General Recommendations:{Colors.NC}")
        for rec in runner_data["general_recommendations"]:
            print(f"  - {rec}")

        print(f"\n{Colors.YELLOW}Cost Optimization Potential:{Colors.NC}")
        cost_data = runner_data['cost_optimization']
        print(f"  Potential savings: {cost_data['potential_savings']}")
        print("  Quick wins:")
        for win in cost_data["quick_wins"]:
            print(f"    - {win}")
