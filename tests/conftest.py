"""Test configuration and fixtures for pytest."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def extension_path():
    """Return the path to the gh-actions-optimizer extension."""
    return Path(__file__).parent.parent / "gh-actions-optimizer"


@pytest.fixture
def mock_gh_command(monkeypatch):
    """Mock the gh command for testing."""

    def mock_run(*args, **kwargs):
        # Mock successful gh command execution
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout='{"mock": "data"}', stderr=""
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    return mock_run
