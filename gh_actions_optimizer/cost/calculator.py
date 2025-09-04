"""Cost calculation utilities."""

from typing import Dict, List


def get_runner_costs() -> Dict[str, float]:
    """Get current GitHub Actions runner costs per minute in USD."""
    return {
        "ubuntu-latest": 0.008,
        "ubuntu-22.04": 0.008,
        "ubuntu-20.04": 0.008,
        "windows-latest": 0.016,
        "windows-2022": 0.016,
        "windows-2019": 0.016,
        "macos-latest": 0.08,
        "macos-14": 0.08,
        "macos-13": 0.08,
        "macos-12": 0.08,
        "macos-latest-xlarge": 0.16,
        "macos-14-xlarge": 0.16,
    }


def get_optimization_tips() -> List[str]:
    """Get cost optimization tips."""
    return [
        "Use ubuntu-latest for most jobs (cheapest)",
        "Only use macOS/Windows when platform-specific testing needed",
        "Enable concurrency controls to prevent redundant runs",
        "Use caching to reduce build times",
        "Consider self-hosted runners for high-volume usage",
    ]


def calculate_workflow_cost(
    runner_type: str, duration_minutes: float, costs: Dict[str, float]
) -> float:
    """Calculate cost for a workflow run."""
    cost_per_minute = costs.get(runner_type, 0.0)
    return cost_per_minute * duration_minutes


def estimate_monthly_cost(
    daily_runs: int, avg_duration_minutes: float, runner_type: str
) -> float:
    """Estimate monthly cost for a workflow."""
    costs = get_runner_costs()
    cost_per_run = calculate_workflow_cost(runner_type, avg_duration_minutes, costs)
    monthly_runs = daily_runs * 30
    return cost_per_run * monthly_runs
