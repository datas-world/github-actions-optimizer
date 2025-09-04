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

# Extension metadata - read version from pyproject.toml
import sys
from pathlib import Path
from typing import Any, Dict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _get_version() -> str:
    """Get version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            pyproject_data: Dict[str, Any] = tomllib.load(f)
        return f"v{pyproject_data['project']['version']}"
    except (FileNotFoundError, KeyError, Exception):
        # Fallback version if pyproject.toml is not found or malformed
        return "v0.1.0-dev"


__version__ = _get_version()
__name__ = "gh-actions-optimizer"
__description__ = (
    "Optimize GitHub Actions workflows for cost, performance, and security"
)

# Package exports
from .main import main

__all__ = ["main", "__version__", "__name__", "__description__"]
