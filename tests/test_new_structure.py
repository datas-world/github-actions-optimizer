"""Tests for the new package structure."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def new_extension_path():
    """Return the path to the new gh-actions-optimizer extension."""
    return Path(__file__).parent.parent / "gh-actions-optimizer-new"


def test_new_extension_executable(new_extension_path):
    """Test that the new extension is executable."""
    assert new_extension_path.exists()
    assert new_extension_path.is_file()
    # Check if file is executable
    assert new_extension_path.stat().st_mode & 0o111


def test_new_extension_help(new_extension_path):
    """Test that the new extension shows help."""
    result = subprocess.run(
        [sys.executable, str(new_extension_path), "--help"],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "Optimize GitHub Actions workflows" in result.stdout
    assert "analyze" in result.stdout
    assert "cost" in result.stdout
    assert "security" in result.stdout
    assert "runners" in result.stdout


def test_new_extension_version(new_extension_path):
    """Test that the new extension shows version."""
    result = subprocess.run(
        [sys.executable, str(new_extension_path), "--version"],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "actions-optimizer" in result.stdout
    assert "v0.1.0-dev" in result.stdout


def test_new_cost_command(new_extension_path):
    """Test the cost command with new structure."""
    result = subprocess.run(
        [sys.executable, str(new_extension_path), "cost", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "runner_costs_per_minute" in result.stdout
    assert "ubuntu-latest" in result.stdout


def test_new_analyze_sample_data(new_extension_path):
    """Test the analyze command with sample data."""
    result = subprocess.run(
        [
            sys.executable,
            str(new_extension_path),
            "analyze",
            "--sample-data",
            "--format",
            "json"
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "workflows" in result.stdout
    assert "sample/repo" in result.stdout


def test_package_imports():
    """Test that the package can be imported correctly."""
    try:
        import gh_actions_optimizer
        assert hasattr(gh_actions_optimizer, 'main')
        assert hasattr(gh_actions_optimizer, '__version__')
        assert gh_actions_optimizer.__version__ == "v0.1.0-dev"
    except ImportError as e:
        pytest.fail(f"Failed to import package: {e}")


def test_subpackage_imports():
    """Test that subpackages can be imported."""
    try:
        from gh_actions_optimizer.shared import log_info, Colors
        from gh_actions_optimizer.analyze import cmd_analyze
        from gh_actions_optimizer.cost import cmd_cost

        # Test that functions are callable
        assert callable(log_info)
        assert callable(cmd_analyze)
        assert callable(cmd_cost)

        # Test Colors class
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'GREEN')

    except ImportError as e:
        pytest.fail(f"Failed to import subpackages: {e}")


def test_implemented_commands(new_extension_path):
    """Test that all commands are now implemented and working."""
    commands = ["security", "runners", "benchmark"]

    for command in commands:
        result = subprocess.run(
            [sys.executable, str(new_extension_path), command, "--quiet"],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        # Commands should produce actual output, not stub messages
        assert "to be implemented" not in result.stderr
