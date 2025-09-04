"""Workflow analysis functions."""

from typing import Any, Dict

from ..shared import log_info


def analyze_workflow(content: str, name: str) -> Dict[str, Any]:
    """Analyze workflow for optimization opportunities."""
    log_info(f"Analyzing workflow: {name}")

    issues = []
    recommendations = []

    # Check for expensive runners
    if "macos" in content.lower() or "windows" in content.lower():
        issues.append("Uses expensive runners (macOS/Windows)")
        recommendations.append(
            "Consider using ubuntu-latest for non-platform-specific jobs"
        )

    # Check for missing concurrency controls
    if "concurrency:" not in content:
        issues.append("Missing concurrency controls")
        recommendations.append("Add concurrency controls to prevent redundant runs")

    # Check for missing cache
    setup_actions = ["setup-node", "setup-python", "setup-java", "setup-go"]
    if any(action in content for action in setup_actions) and "cache:" not in content:
        issues.append("Missing dependency caching")
        recommendations.append("Enable caching for faster builds and reduced costs")

    # Check for security issues
    if "pull_request_target" in content:
        issues.append("Uses potentially unsafe pull_request_target trigger")
        recommendations.append(
            "Review pull_request_target usage for security implications"
        )

    # Check for hardcoded secrets
    if "${{" in content and any(
        secret in content.upper() for secret in ["PASSWORD", "TOKEN", "KEY", "SECRET"]
    ):
        issues.append("Potential hardcoded secrets detected")
        recommendations.append(
            "Ensure all secrets use GitHub secrets or environment variables"
        )

    return {
        "name": name,
        "issues": issues,
        "recommendations": recommendations,
        "has_issues": len(issues) > 0,
    }
