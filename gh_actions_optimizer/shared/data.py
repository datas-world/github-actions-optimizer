"""Sample data generators and utilities."""

from typing import Any


def get_sample_workflows() -> list[dict[str, Any]]:
    """Get sample workflow data for testing."""
    return [
        {
            "name": "ci.yml",
            "download_url": "sample",
            "content": """
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest
""",
        },
        {
            "name": "security.yml",
            "download_url": "sample",
            "content": """
name: Security
on: [push]
jobs:
  security:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - run: bandit -r .
""",
        },
    ]


def get_sample_security_data() -> dict[str, Any]:
    """Get sample security data for testing."""
    return {
        "has_vulnerability_alerts": True,
        "has_dependabot_alerts": True,
        "has_automated_security_fixes": False,
        "security_and_analysis": {
            "secret_scanning": {"status": "enabled"},
            "dependabot_security_updates": {"status": "disabled"},
        },
    }


def generate_sample_security_issues() -> list[dict[str, Any]]:
    """Generate sample security issues for testing."""
    return [
        {
            "workflow": "ci.yml",
            "issues": [
                "Missing explicit permissions",
                "Missing timeout configuration"
            ],
            "severity": "MEDIUM"
        },
        {
            "workflow": "deploy.yml",
            "issues": [
                "Direct secrets usage detected",
                "Action not pinned to specific version: actions/checkout@main"
            ],
            "severity": "HIGH"
        },
        {
            "workflow": "security.yml",
            "issues": [
                "Uses expensive macOS runners",
                "Missing concurrency control"
            ],
            "severity": "MEDIUM"
        }
    ]
