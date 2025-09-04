"""Tests for GitHub Actions security hardening."""

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml


class TestSecurityHardening:
    """Test security hardening measures in workflows."""

    @pytest.fixture
    def workflow_files(self) -> Dict[str, Dict[Any, Any]]:
        """Load all workflow YAML files."""
        workflows_dir = Path(__file__).parent.parent / ".github" / "workflows"
        workflow_files = {}

        for workflow_path in workflows_dir.glob("*.yml"):
            with open(workflow_path, "r") as f:
                workflow_files[workflow_path.name] = yaml.safe_load(f)

        return workflow_files

    def test_all_actions_pinned_to_commit_sha(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that all GitHub Actions are pinned to specific commit SHAs."""
        unpinned_actions = []

        for workflow_name, workflow_content in workflow_files.items():
            jobs = workflow_content.get("jobs", {})

            for job_name, job_content in jobs.items():
                steps = job_content.get("steps", [])

                for step in steps:
                    if "uses" in step:
                        action = step["uses"]

                        # Check if action uses @main, @master, or version tags
                        if "@main" in action or "@master" in action:
                            unpinned_actions.append(
                                f"{workflow_name}:{job_name} - {action}"
                            )
                        elif re.match(r".*@v?\d+(\.\d+)*$", action):
                            unpinned_actions.append(
                                f"{workflow_name}:{job_name} - {action}"
                            )

        assert not unpinned_actions, f"Found unpinned actions: {unpinned_actions}"

    def test_explicit_permissions_defined(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that all workflows have explicit permissions defined."""
        workflows_without_permissions = []

        for workflow_name, workflow_content in workflow_files.items():
            # Check for global permissions or job-level permissions
            has_global_permissions = "permissions" in workflow_content

            jobs = workflow_content.get("jobs", {})
            all_jobs_have_permissions = True

            for job_name, job_content in jobs.items():
                if "permissions" not in job_content:
                    all_jobs_have_permissions = False
                    break

            # Workflow should have either global permissions or all jobs should have permissions
            if not has_global_permissions and not all_jobs_have_permissions:
                workflows_without_permissions.append(workflow_name)

        assert (
            not workflows_without_permissions
        ), f"Workflows without explicit permissions: {workflows_without_permissions}"

    def test_minimal_permissions_principle(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that workflows follow the principle of least privilege."""
        overly_broad_permissions = []

        for workflow_name, workflow_content in workflow_files.items():
            # Check global permissions
            global_permissions = workflow_content.get("permissions", {})
            if isinstance(global_permissions, dict) and global_permissions:
                # Should not have write permissions to all scopes
                write_permissions = [
                    key for key, value in global_permissions.items() if value == "write"
                ]
                if (
                    len(write_permissions) > 3
                ):  # More than 3 write permissions is suspicious
                    overly_broad_permissions.append(
                        f"{workflow_name} (global): {write_permissions}"
                    )

            # Check job-level permissions
            jobs = workflow_content.get("jobs", {})
            for job_name, job_content in jobs.items():
                job_permissions = job_content.get("permissions", {})
                if isinstance(job_permissions, dict) and job_permissions:
                    write_permissions = [
                        key
                        for key, value in job_permissions.items()
                        if value == "write"
                    ]
                    if (
                        len(write_permissions) > 2
                    ):  # Jobs should have minimal write permissions
                        overly_broad_permissions.append(
                            f"{workflow_name}:{job_name}: {write_permissions}"
                        )

        # Allow some exceptions for legitimate use cases
        exceptions = [
            "main.yml:pre-commit",  # Needs contents:write for auto-updates
        ]

        filtered_issues = [
            issue
            for issue in overly_broad_permissions
            if not any(exception in issue for exception in exceptions)
        ]

        assert (
            not filtered_issues
        ), f"Workflows with overly broad permissions: {filtered_issues}"

    def test_concurrency_controls_implemented(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that all workflows have concurrency controls."""
        workflows_without_concurrency = []

        for workflow_name, workflow_content in workflow_files.items():
            if "concurrency" not in workflow_content:
                workflows_without_concurrency.append(workflow_name)

        assert (
            not workflows_without_concurrency
        ), f"Workflows without concurrency controls: {workflows_without_concurrency}"

    def test_no_direct_secrets_usage(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that workflows don't have hardcoded secrets."""
        workflows_with_direct_secrets = []

        for workflow_name, workflow_content in workflow_files.items():
            # Convert to string to search for patterns
            workflow_str = yaml.dump(workflow_content)

            # Look for suspicious patterns (excluding legitimate GitHub secrets usage)
            suspicious_patterns = [
                r"password:\s*['\"][^'\"]*['\"]",
                r"token:\s*['\"][^'\"]*['\"]",
                r"key:\s*['\"][^'\"]*['\"]",
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, workflow_str, re.IGNORECASE):
                    # Exclude legitimate GitHub secrets usage
                    if not re.search(r"\$\{\{\s*secrets\.", workflow_str):
                        workflows_with_direct_secrets.append(workflow_name)
                        break

        assert (
            not workflows_with_direct_secrets
        ), f"Workflows with potential hardcoded secrets: {workflows_with_direct_secrets}"

    def test_timeout_limits_configured(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that all jobs have reasonable timeout limits."""
        jobs_without_timeout = []
        jobs_with_excessive_timeout = []

        for workflow_name, workflow_content in workflow_files.items():
            jobs = workflow_content.get("jobs", {})

            for job_name, job_content in jobs.items():
                timeout = job_content.get("timeout-minutes")

                if timeout is None:
                    jobs_without_timeout.append(f"{workflow_name}:{job_name}")
                elif timeout > 60:  # More than 1 hour is excessive for most jobs
                    jobs_with_excessive_timeout.append(
                        f"{workflow_name}:{job_name} ({timeout}min)"
                    )

        assert (
            not jobs_without_timeout
        ), f"Jobs without timeout limits: {jobs_without_timeout}"

        assert (
            not jobs_with_excessive_timeout
        ), f"Jobs with excessive timeout: {jobs_with_excessive_timeout}"

    def test_no_pull_request_target_without_safety(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that pull_request_target is used safely."""
        unsafe_pull_request_target = []

        for workflow_name, workflow_content in workflow_files.items():
            # Check for pull_request_target trigger
            triggers = workflow_content.get("on", workflow_content.get(True, {}))

            if "pull_request_target" in triggers:
                # Should have safety checks
                workflow_str = yaml.dump(workflow_content)
                safety_checks = [
                    "github.event_name != 'pull_request_target'",
                    "github.actor == 'dependabot[bot]'",
                    "contains(github.event.pull_request.labels.*.name, 'safe')",
                ]

                has_safety_check = any(check in workflow_str for check in safety_checks)

                if not has_safety_check:
                    unsafe_pull_request_target.append(workflow_name)

        assert (
            not unsafe_pull_request_target
        ), f"Workflows with unsafe pull_request_target: {unsafe_pull_request_target}"

    def test_runner_security_appropriate(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that appropriate runners are used for security levels."""
        insecure_runner_usage = []

        for workflow_name, workflow_content in workflow_files.items():
            jobs = workflow_content.get("jobs", {})

            for job_name, job_content in jobs.items():
                runs_on = job_content.get("runs-on", "")

                # Check for self-hosted runners without proper security context
                if "self-hosted" in runs_on:
                    # Should have additional security considerations
                    # For now, flag for manual review
                    insecure_runner_usage.append(f"{workflow_name}:{job_name}")

        # Currently no self-hosted runners, so this should pass
        assert (
            not insecure_runner_usage
        ), f"Jobs using potentially insecure runners: {insecure_runner_usage}"

    def test_action_version_comments_present(
        self, workflow_files: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test that actions with commit SHAs have version comments."""
        actions_without_version_comments = []

        for workflow_name, workflow_content in workflow_files.items():
            # Read the raw file to check for comments
            workflow_path = (
                Path(__file__).parent.parent / ".github" / "workflows" / workflow_name
            )

            with open(workflow_path, "r") as f:
                workflow_text = f.read()

            # Find actions with commit SHAs
            action_lines = re.findall(r"uses: .+@[a-f0-9]{40}.*", workflow_text)

            for line in action_lines:
                # Check if the line has a version comment
                if "# v" not in line:
                    actions_without_version_comments.append(
                        f"{workflow_name}: {line.strip()}"
                    )

        assert (
            not actions_without_version_comments
        ), f"Actions without version comments: {actions_without_version_comments}"
