#!/usr/bin/env python3
"""Simple test script for the refactored package."""

import subprocess
import sys
from pathlib import Path


def test_imports() -> None:
    """Test package imports."""
    print("Testing package imports...")

    import gh_actions_optimizer

    print(f"✓ Main package imported, version: {gh_actions_optimizer.__version__}")

    print("✓ Shared utilities imported")

    print("✓ Analyze command imported")

    print("✓ Cost command imported")

    # Assert that we successfully imported and have version
    assert hasattr(gh_actions_optimizer, "__version__")
    assert gh_actions_optimizer.__version__ is not None


def test_entry_point() -> None:
    """Test the entry point."""
    print("\nTesting entry point...")

    entry_point = Path("gh-actions-optimizer")
    assert entry_point.exists(), "✗ Entry point not found"

    # Test help command
    result = subprocess.run(
        [sys.executable, str(entry_point), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"✗ Help command failed: {result.stderr}"
    print("✓ Help command works")

    # Test cost command
    result = subprocess.run(
        [sys.executable, str(entry_point), "cost", "--quiet"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"✗ Cost command failed: {result.stderr}"
    assert (
        "ubuntu-latest" in result.stdout
    ), "✗ Cost command output missing expected content"
    print("✓ Cost command works")

    # Test analyze with sample data
    result = subprocess.run(
        [
            sys.executable,
            str(entry_point),
            "analyze",
            "--sample-data",
            "--quiet",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"✗ Analyze command failed: {result.stderr}"
    assert (
        "ci.yml" in result.stdout
    ), "✗ Analyze command output missing expected content"
