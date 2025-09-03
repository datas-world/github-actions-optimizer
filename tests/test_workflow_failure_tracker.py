"""Tests for the workflow failure tracker."""

import yaml
import pytest
import re
from pathlib import Path


class TestWorkflowFailureTracker:
    """Test the workflow failure tracker configuration."""

    @pytest.fixture
    def workflow_file(self):
        """Load the workflow failure tracker YAML file."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "workflow-failure-tracker.yml"
        with open(workflow_path, "r") as f:
            return yaml.safe_load(f)

    def test_workflow_triggers_on_correct_events(self, workflow_file):
        """Test that the workflow triggers on the correct events."""
        # In YAML, 'on' is a reserved word in Python and becomes True when parsed by PyYAML
        # This is documented in PyYAML's documentation and is a known behavior
        # See: https://pyyaml.org/wiki/PyYAMLDocumentation
        # Alternative approaches: use safe_load with custom constructor or check both keys
        assert True in workflow_file or "on" in workflow_file
        workflow_run_config = workflow_file.get(True, workflow_file.get("on", {}))["workflow_run"]
        
        # Should trigger on these specific workflows
        expected_workflows = ["CI", "CodeQL Analysis", "Pre-commit"]
        assert workflow_run_config["workflows"] == expected_workflows
        
        # Should only trigger on completed events
        assert workflow_run_config["types"] == ["completed"]

    def test_workflow_has_correct_permissions(self, workflow_file):
        """Test that the workflow has the necessary permissions."""
        permissions = workflow_file.get("permissions", {})
        
        # Required permissions for the workflow to function
        assert permissions.get("contents") == "read"
        assert permissions.get("issues") == "write"
        assert permissions.get("actions") == "read"

    def test_workflow_has_failure_condition(self, workflow_file):
        """Test that the workflow only runs on failures."""
        jobs = workflow_file.get("jobs", {})
        track_failures = jobs.get("track-failures", {})
        
        # Should only run when the workflow run conclusion is failure and not on PR-related events
        expected_condition = "${{ github.event.workflow_run.conclusion == 'failure' && github.event.workflow_run.event != 'pull_request' && github.event.workflow_run.event != 'pull_request_review' && github.event.workflow_run.event != 'pull_request_review_comment' && github.event.workflow_run.event != 'pull_request_target' }}"
        assert track_failures.get("if") == expected_condition

    def test_workflow_structure_is_valid(self, workflow_file):
        """Test that the workflow has a valid structure."""
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

    def test_workflow_has_required_steps(self, workflow_file):
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
            "Update existing issue"
        ]
        
        for required_step in required_steps:
            assert required_step in step_names, f"Missing required step: {required_step}"

    def test_workflow_uses_correct_actions(self, workflow_file):
        """Test that the workflow uses the correct GitHub actions."""
        jobs = workflow_file["jobs"]
        track_failures = jobs["track-failures"]
        steps = track_failures["steps"]
        
        # Check for specific actions
        actions_used = []
        for step in steps:
            if "uses" in step:
                actions_used.append(step["uses"])
        
        # Expected actions
        expected_actions = [
            "actions/checkout@v4"
        ]
        
        for expected_action in expected_actions:
            # GitHub action names follow the pattern: owner/repo@ref
            # According to GitHub docs: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsuses
            # Action references can contain '@' only as separator between action and version/ref
            # Valid formats: owner/repo@ref, ./path/to/action, docker://image:tag
            # We use regex validation for robustness instead of simple string splitting
            action_pattern = re.compile(r'^([^@/]+/[^@/]+)@(.+)$|^\./.+$|^docker://.+$')
            
            for action in actions_used:
                if not action_pattern.match(action):
                    pytest.fail(f"Invalid action format: {action}")
                    
                # Extract action name (part before @) for comparison
                if '@' in action:
                    action_name = action.split('@')[0]
                else:
                    action_name = action
                    
                if expected_action.split('@')[0] in action_name:
                    break
            else:
                pytest.fail(f"Missing expected action: {expected_action}")

    def test_workflow_timeout_is_reasonable(self, workflow_file):
        """Test that the workflow has a reasonable timeout."""
        jobs = workflow_file["jobs"]
        track_failures = jobs["track-failures"]
        
        # Should have a timeout to prevent hanging
        assert "timeout-minutes" in track_failures
        timeout = track_failures["timeout-minutes"]
        
        # Should be reasonable (not too short, not too long)
        assert 5 <= timeout <= 30, f"Timeout should be between 5-30 minutes, got {timeout}"

    def test_conditional_steps_exist(self, workflow_file):
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
        
        assert create_issue_step.get("if") == "steps.check-issue.outputs.issue_exists == 'false'"
        assert update_issue_step.get("if") == "steps.check-issue.outputs.issue_exists == 'true'"

    def test_workflow_outputs_are_properly_set(self, workflow_file):
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
            "workflow_head_branch"
        ]
        
        for output in expected_outputs:
            assert f"echo \"{output}=" in run_commands, f"Missing output: {output}"