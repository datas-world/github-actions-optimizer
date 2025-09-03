#!/usr/bin/env python3
"""Simple test script for the refactored package."""

import sys
import subprocess
from pathlib import Path


def test_imports():
    """Test package imports."""
    print("Testing package imports...")

    try:
        import gh_actions_optimizer
        print(
            f"✓ Main package imported, version: {gh_actions_optimizer.__version__}")

        from gh_actions_optimizer.shared import log_info, Colors
        print("✓ Shared utilities imported")

        from gh_actions_optimizer.analyze import cmd_analyze
        print("✓ Analyze command imported")

        from gh_actions_optimizer.cost import cmd_cost
        print("✓ Cost command imported")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_entry_point():
    """Test the new entry point."""
    print("\nTesting entry point...")

    entry_point = Path("gh-actions-optimizer-new")
    if not entry_point.exists():
        print("✗ Entry point not found")
        return False

    # Test help command
    result = subprocess.run(
        [sys.executable, str(entry_point), "--help"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0:
        print("✓ Help command works")
    else:
        print(f"✗ Help command failed: {result.stderr}")
        return False

    # Test cost command
    result = subprocess.run(
        [sys.executable, str(entry_point), "cost", "--quiet"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0 and "ubuntu-latest" in result.stdout:
        print("✓ Cost command works")
    else:
        print(f"✗ Cost command failed: {result.stderr}")
        return False

    # Test analyze with sample data
    result = subprocess.run(
        [sys.executable, str(entry_point), "analyze",
         "--sample-data", "--quiet"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0 and "ci.yml" in result.stdout:
        print("✓ Analyze command works")
    else:
        print(f"✗ Analyze command failed: {result.stderr}")
        return False

    return True


def main():
    """Run all tests."""
    print("=== Testing Refactored GitHub Actions Optimizer ===\n")

    imports_ok = test_imports()
    entry_point_ok = test_entry_point()

    print(f"\n=== Results ===")
    print(f"Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Entry Point: {'✓ PASS' if entry_point_ok else '✗ FAIL'}")

    if imports_ok and entry_point_ok:
        print("\n🎉 All tests passed! The refactoring was successful.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
