"""Test configuration and fixtures for pytest."""

import subprocess
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def extension_path() -> Path:
    """Return the path to the gh-actions-optimizer extension."""
    return Path(__file__).parent.parent / "gh-actions-optimizer"


@pytest.fixture
def mock_gh_command(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Mock the gh command for testing."""

    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        # Mock successful gh command execution
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout='{"mock": "data"}', stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    return mock_run
