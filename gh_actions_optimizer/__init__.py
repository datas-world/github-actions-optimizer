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

import semver


class _VersionManager:
    """Manages package version with caching."""

    @functools.cached_property
    def __version__(self) -> str:
        """Get and validate version from package metadata with caching.

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


# Create singleton instance for version management
_version_manager = _VersionManager()

# Package metadata - single source of truth for version
__version__ = _version_manager.__version__
__name__ = "gh-actions-optimizer"
__description__ = (
    "Optimize GitHub Actions workflows for cost, performance, and security"
)

# Package exports
from .main import main  # noqa: E402

__all__ = ["main", "__version__", "__name__", "__description__"]
