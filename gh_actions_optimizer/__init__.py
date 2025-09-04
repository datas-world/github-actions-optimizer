"""GitHub Actions Optimizer - GitHub CLI Extension.

A comprehensive GitHub CLI extension for optimizing GitHub Actions workflows
through cost analysis, performance optimization, and security auditing.

Features:
- Workflow analysis and optimization recommendations
- Cost calculation and optimization strategies
- Security auditing and compliance checks
- Runner optimization suggestions
- Integration with GitHub API via gh CLI
"""

# Extension metadata
__version__ = "v0.1.0-dev"
__name__ = "actions-optimizer"
__description__ = (
    "Optimize GitHub Actions workflows for cost, performance, and security"
)

# Package exports
from .main import main

__all__ = ["main", "__version__", "__name__", "__description__"]
