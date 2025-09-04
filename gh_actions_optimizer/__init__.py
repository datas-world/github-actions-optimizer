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

# Extension metadata - use importlib.metadata for proper version handling
import functools
import importlib.metadata
from typing import Optional

import semver


@functools.lru_cache(maxsize=1)
def _get_version() -> str:
    """Get and validate version from package metadata.

    Returns:
        Validated semantic version string with 'v' prefix.

    Raises:
        RuntimeError: If version cannot be determined or is invalid.
    """
    try:
        # Try to get version from installed package metadata
        version = importlib.metadata.version("github-actions-optimizer")

        # Normalize version format (remove .dev0 suffix for semver validation)
        normalized_version = version.replace(".dev0", "-dev")

        # Validate that it's a proper semantic version
        try:
            semver.VersionInfo.parse(normalized_version)
        except ValueError as e:
            raise RuntimeError(f"Invalid semantic version '{version}': {e}") from e

        return f"v{version}"

    except importlib.metadata.PackageNotFoundError as e:
        raise RuntimeError(
            "Package 'github-actions-optimizer' not found. "
            "This indicates an installation issue."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to determine package version: {e}") from e


# Cached version property
__version__: Optional[str] = None


def get_version() -> str:
    """Get the cached version or compute it if not cached."""
    global __version__
    if __version__ is None:
        __version__ = _get_version()
    return __version__


# Package metadata
__version__ = get_version()
__name__ = "gh-actions-optimizer"
__description__ = (
    "Optimize GitHub Actions workflows for cost, performance, and security"
)

# Package exports
from .main import main  # noqa: E402

__all__ = ["main", "__version__", "__name__", "__description__", "get_version"]
