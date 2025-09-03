"""Basic tests for the GitHub CLI extension."""

import subprocess
import sys
from pathlib import Path

import pytest


def test_extension_executable(extension_path):
    """Test that the extension is executable."""
    assert extension_path.exists()
    assert extension_path.is_file()
    # Check if file is executable
    assert extension_path.stat().st_mode & 0o111


def test_extension_help(extension_path):
    """Test that the extension shows help."""
    result = subprocess.run(
        [sys.executable, str(extension_path), "--help"],
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


def test_extension_version(extension_path):
    """Test that the extension shows version."""
    result = subprocess.run(
        [sys.executable, str(extension_path), "--version"],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "actions-optimizer" in result.stdout
    assert "v0.1.0-dev" in result.stdout


def test_cost_command(extension_path):
    """Test the cost command."""
    result = subprocess.run(
        [sys.executable, str(extension_path), "cost", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "runner_costs_per_minute" in result.stdout
    assert "ubuntu-latest" in result.stdout


def test_runners_command(extension_path):
    """Test the runners command."""
    result = subprocess.run(
        [sys.executable, str(extension_path), "runners", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0
    assert "general_recommendations" in result.stdout
