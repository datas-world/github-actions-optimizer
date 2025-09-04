"""Tests for the workflow failure tracker."""

import re
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml


class TestWorkflowFailureTracker:
    """Test the workflow failure tracker configuration."""

    @pytest.fixture
    def workflow_file(self) -> Dict[Any, Any]:
        """Load the workflow failure tracker YAML file."""
        workflow_path = (
            Path(__file__).parent.parent
            / ".github"
            / "workflows"
            / "workflow-failure-tracker.yml"
        )
        with open(workflow_path, "r") as f:
            return yaml.safe_load(f)  # type: ignore[no-any-return]

    def test_workflow_triggers_on_all_workflows(
        self, workflow_file: Dict[Any, Any]
    ) -> None:
        """Test that the workflow triggers on all workflows.

        Implementation note: PyYAML automatically converts the YAML 'on'
        keyword to Python's boolean True when parsing. This is documented
        behavior per the YAML 1.1 specification and PyYAML implementation:

        - https://yaml.org/type/bool.html (YAML 1.1 specification)
        - https://pyyaml.org/wiki/PyYAMLDocumentation
        - GitHub issue: https://github.com/yaml/pyyaml/issues/98

        The YAML boolean type includes:
        y|Y|yes|Yes|YES|n|N|no|No|NO|true|True|TRUE|false|False|FALSE|
        on|On|ON|off|Off|OFF

        Since 'on' appears in this list, PyYAML treats it as a boolean value.

        Alternative solutions:
        1. Use yaml.safe_load() with custom constructors
        2. Check for both 'on' and True keys as we do here
        3. Use ruamel.yaml which preserves the original key names
        """
        # Check both possible key representations due to PyYAML's boolean
        # conversion
        assert True in workflow_file or "on" in workflow_file
        workflow_run_config = workflow_file.get(True, workflow_file.get("on", {}))[
            "workflow_run"
        ]

        # Should not have hardcoded workflows - should monitor all workflows
        assert (
            "workflows" not in workflow_run_config
        ), "Workflow should not hardcode specific workflow names"

        # Should only trigger on completed events
        assert workflow_run_config["types"] == ["completed"]

    def test_workflow_has_correct_permissions(
        self, workflow_file: Dict[Any, Any]
    ) -> None:
        """Test that the workflow has the necessary permissions."""
        permissions = workflow_file.get("permissions", {})

        # Required permissions for the workflow to function
        assert permissions.get("contents") == "read"
        assert permissions.get("issues") == "write"
        assert permissions.get("actions") == "read"

    def test_workflow_has_failure_condition(
        self, workflow_file: Dict[Any, Any]
    ) -> None:
        """Test that the workflow only runs on failures."""
        jobs = workflow_file.get("jobs", {})
        track_failures = jobs.get("track-failures", {})

        # Should only run when the workflow run conclusion is failure
        # and not on PR-related events, OR on scheduled self-monitoring
        expected_condition = (
            "${{ (github.event_name == 'workflow_run' && "
            "github.event.workflow_run.conclusion == 'failure' && "
            "github.event.workflow_run.event != 'pull_request' && "
            "github.event.workflow_run.event != 'pull_request_review' && "
            "github.event.workflow_run.event != 'pull_request_review_comment' && "
            "github.event.workflow_run.event != 'pull_request_target') || "
            "github.event_name == 'schedule' }}"
        )
        assert track_failures.get("if") == expected_condition

    def test_workflow_structure_is_valid(self, workflow_file: Dict[Any, Any]) -> None:
        """Test that the workflow has a valid structure.

        Implementation note: The 'on' keyword handling is explained above.
        We validate the basic GitHub Actions workflow structure:
        - 'name': Required workflow name
        - 'on'/'True': Trigger configuration (parsed as boolean by PyYAML)
        - 'jobs': Job definitions

        Reference: https://docs.github.com/en/actions/using-workflows/
        workflow-syntax-for-github-actions
        """
        # Basic structure validation
        assert "name" in workflow_file
        # 'on' keyword becomes True in YAML parsing due to PyYAML's implicit boolean conversion
        # See: https://yaml.org/type/bool.html and https://pyyaml.org/wiki/PyYAMLDocumentation
        assert True in workflow_file or "on" in workflow_file
        assert "jobs" in workflow_file

        # Job structure validation
        jobs = workflow_file["jobs"]
        assert "track-failures" in jobs

        track_failures = jobs["track-failures"]
        assert "runs-on" in track_failures
        assert "steps" in track_failures
        assert track_failures["runs-on"] == "ubuntu-latest"

    def test_workflow_has_required_steps(self, workflow_file: Dict[Any, Any]) -> None:
        """Test that the workflow has all required steps."""
        jobs = workflow_file["jobs"]
        track_failures = jobs["track-failures"]
        steps = track_failures["steps"]

        step_names = [step.get("name", "") for step in steps]

        # Required steps for the workflow to function
        required_steps = [
            "Checkout repository",
            "Get workflow run details",
            "Check for existing issue",
            "Create new issue",
            "Update existing issue",
        ]

        for required_step in required_steps:
            assert (
                required_step in step_names
            ), f"Missing required step: {required_step}"

    def test_workflow_uses_correct_actions(self, workflow_file: Dict[Any, Any]) -> None:
        """Test that the workflow uses the correct GitHub actions.

        This test validates GitHub action name formats with comprehensive
        regex validation and fail-safe handling for multiple '@' symbols.

        Documentation references:
        - GitHub Actions syntax: https://docs.github.com/en/actions/
          using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsuses
        - Action versioning: https://docs.github.com/en/actions/
          creating-actions/about-custom-actions#using-versioning-in-actions
        - Repository naming rules: https://docs.github.com/en/repositories/
          creating-and-managing-repositories/about-repositories#repository-names

        Security considerations:
        - Repository names cannot contain '@' per GitHub naming rules
        - Only one '@' is valid in action references (separates action from
          version/ref)
        - Multiple '@' symbols indicate malformed or potentially malicious
          syntax
        """
        jobs = workflow_file["jobs"]
        track_failures = jobs["track-failures"]
        steps = track_failures["steps"]

        # Check for specific actions
        actions_used = []
        for step in steps:
            if "uses" in step:
                actions_used.append(step["uses"])

        # Expected actions with comprehensive validation
        expected_actions = ["actions/checkout@v4"]

        # Comprehensive GitHub action name validation pattern
        # Based on official GitHub documentation and security best practices
        action_pattern = re.compile(
            r"^([a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+)@([a-zA-Z0-9\-_.]+)$|"
            r"^\./.+$|"  # Local action: ./path/to/action
            r"^docker://[^@\s]+$"  # Docker action: docker://image:tag
        )

        for expected_action in expected_actions:
            # Validate all used actions for security and format compliance
            for action in actions_used:
                # Fail-safe validation for multiple '@' symbols
                at_count = action.count("@")
                if at_count > 1:
                    pytest.fail(
                        f"Action contains multiple '@' symbols "
                        f"(security risk): {action}"
                    )

                # Comprehensive regex validation
                if not action_pattern.match(action):
                    pytest.fail(f"Invalid action format: {action}")

                # Safe extraction with proper error handling
                if "@" in action and at_count == 1:
                    action_name = action.split("@")[0]
                else:
                    action_name = action

                # Check if expected action is present
                expected_name = expected_action.split("@")[0]
                if expected_name in action_name:
                    break
            else:
                pytest.fail(f"Missing expected action: {expected_action}")

    def test_workflow_timeout_is_reasonable(
        self, workflow_file: Dict[Any, Any]
    ) -> None:
        """Test that the workflow has a reasonable timeout."""
        jobs = workflow_file["jobs"]
        track_failures = jobs["track-failures"]

        # Should have a timeout to prevent hanging
        assert "timeout-minutes" in track_failures
        timeout = track_failures["timeout-minutes"]

        # Should be reasonable (not too short, not too long)
        assert (
            5 <= timeout <= 30
        ), f"Timeout should be between 5-30 minutes, got {timeout}"

    def test_conditional_steps_exist(self, workflow_file: Dict[Any, Any]) -> None:
        """Test that conditional steps have proper conditions."""
        jobs = workflow_file["jobs"]
        track_failures = jobs["track-failures"]
        steps = track_failures["steps"]

        # Find conditional steps
        create_issue_step = None
        update_issue_step = None

        for step in steps:
            if step.get("name") == "Create new issue":
                create_issue_step = step
            elif step.get("name") == "Update existing issue":
                update_issue_step = step

        # Verify conditional logic
        assert create_issue_step is not None
        assert update_issue_step is not None

        assert (
            create_issue_step.get("if")
            == "steps.check-issue.outputs.issue_exists == 'false' && steps.workflow-details.outputs.workflow_name != ''"
        )
        assert (
            update_issue_step.get("if")
            == "steps.check-issue.outputs.issue_exists == 'true' && steps.workflow-details.outputs.workflow_name != ''"
        )

    def test_workflow_outputs_are_properly_set(
        self, workflow_file: Dict[Any, Any]
    ) -> None:
        """Test that workflow steps set outputs correctly."""
        jobs = workflow_file["jobs"]
        track_failures = jobs["track-failures"]
        steps = track_failures["steps"]

        # Check workflow details step
        workflow_details_step = None
        for step in steps:
            if step.get("id") == "workflow-details":
                workflow_details_step = step
                break

        assert workflow_details_step is not None

        # Should set various workflow-related outputs
        run_commands = workflow_details_step.get("run", "")
        expected_outputs = [
            "workflow_name",
            "workflow_run_id",
            "workflow_url",
            "workflow_head_sha",
            "workflow_head_branch",
        ]

        for output in expected_outputs:
            assert f'echo "{output}=' in run_commands, f"Missing output: {output}"
