"""Tests for security command functionality."""

import argparse
import json
import yaml
from unittest.mock import Mock, patch, MagicMock
import pytest

from gh_actions_optimizer.security.command import cmd_security


class TestSecurityCommand:
    """Test security command functionality."""

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.data.generate_sample_security_issues")
    def test_cmd_security_with_sample_data(self, mock_sample_data, mock_validate_auth, mock_get_repo):
        """Test security command with sample data."""
        args = Mock(quiet=False, sample_data=True, format="table", output=None)
        mock_get_repo.return_value = "sample/repo"
        mock_validate_auth.return_value = True
        mock_sample_data.return_value = [
            {
                "workflow": "test.yml",
                "issues": ["Missing explicit permissions"],
                "severity": "MEDIUM"
            }
        ]
        
        # Mock the Rich console
        with patch("gh_actions_optimizer.shared.cli.colors") as mock_colors:
            mock_console = Mock()
            mock_colors.get_console.return_value = mock_console
            
            cmd_security(args)
            
            # Verify console.print was called
            assert mock_console.print.call_count > 0

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.data.generate_sample_security_issues")
    def test_cmd_security_auth_failure(self, mock_sample_data, mock_validate_auth, mock_get_repo):
        """Test security command when GitHub auth fails."""
        args = Mock(quiet=False, sample_data=False, format="table", output=None)
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = False
        mock_sample_data.return_value = []
        
        with patch("gh_actions_optimizer.shared.cli.colors") as mock_colors:
            mock_console = Mock()
            mock_colors.get_console.return_value = mock_console
            
            cmd_security(args)
            
            # Should fall back to sample data when auth fails
            mock_sample_data.assert_called_once()

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.github.get_workflows")
    @patch("gh_actions_optimizer.shared.github.download_workflow_content")
    def test_cmd_security_real_workflows(self, mock_download, mock_get_workflows, mock_validate_auth, mock_get_repo):
        """Test security command with real workflow analysis."""
        args = Mock(quiet=False, sample_data=False, format="table", output=None)
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = True
        
        # Mock workflows
        mock_get_workflows.return_value = [
            {
                "name": "ci.yml",
                "download_url": "https://example.com/ci.yml"
            }
        ]
        
        # Mock workflow content with security issues
        workflow_content = """
name: CI
on: [push, pull_request_target]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main
      - run: echo ${{ secrets.API_KEY }}
      - run: echo ${{ github.event.head_commit.message }}
"""
        mock_download.return_value = workflow_content
        
        with patch("gh_actions_optimizer.shared.cli.colors") as mock_colors:
            mock_console = Mock()
            mock_colors.get_console.return_value = mock_console
            
            cmd_security(args)
            
            # Verify analysis was performed
            mock_get_workflows.assert_called_once_with("owner/repo")
            mock_download.assert_called_once_with("https://example.com/ci.yml")

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.github.get_workflows")
    def test_cmd_security_json_output(self, mock_get_workflows, mock_validate_auth, mock_get_repo):
        """Test security command with JSON output."""
        args = Mock(quiet=False, sample_data=False, format="json", output=None)
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = True
        mock_get_workflows.return_value = []
        
        with patch("builtins.print") as mock_print:
            cmd_security(args)
            
            # Verify JSON output was printed
            mock_print.assert_called_once()
            output_json = mock_print.call_args[0][0]
            parsed = json.loads(output_json)
            assert "repository" in parsed
            assert "security_audit" in parsed
            assert "recommendations" in parsed

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.github.get_workflows")
    def test_cmd_security_yaml_output(self, mock_get_workflows, mock_validate_auth, mock_get_repo):
        """Test security command with YAML output."""
        args = Mock(quiet=False, sample_data=False, format="yaml", output=None)
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = True
        mock_get_workflows.return_value = []
        
        with patch("builtins.print") as mock_print:
            cmd_security(args)
            
            # Verify YAML output was printed
            mock_print.assert_called_once()
            output_yaml = mock_print.call_args[0][0]
            parsed = yaml.safe_load(output_yaml)
            assert "repository" in parsed
            assert "security_audit" in parsed
            assert "recommendations" in parsed

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.github.get_workflows")
    @patch("builtins.open", create=True)
    def test_cmd_security_file_output(self, mock_open, mock_get_workflows, mock_validate_auth, mock_get_repo):
        """Test security command with file output."""
        args = Mock(quiet=False, sample_data=False, format="json", output="output.json")
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = True
        mock_get_workflows.return_value = []
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        with patch("gh_actions_optimizer.security.command.log_success") as mock_log_success:
            cmd_security(args)
            
            # Verify file was opened for writing
            mock_open.assert_called_once_with("output.json", "w")
            mock_log_success.assert_called_once()

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.github.get_workflows")
    @patch("gh_actions_optimizer.shared.github.download_workflow_content")
    def test_cmd_security_workflow_analysis_details(self, mock_download, mock_get_workflows, mock_validate_auth, mock_get_repo):
        """Test detailed workflow security analysis."""
        args = Mock(quiet=False, sample_data=False, format="table", output=None)
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = True
        
        mock_get_workflows.return_value = [
            {
                "name": "vulnerable.yml",
                "download_url": "https://example.com/vulnerable.yml"
            }
        ]
        
        # Workflow with multiple security issues
        workflow_content = """
name: Vulnerable Workflow
on: [push, pull_request_target]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main
      - uses: third-party/action@master  
      - run: echo ${{ secrets.API_KEY }}
      - run: echo ${{ github.event.head_commit.message }}
"""
        mock_download.return_value = workflow_content
        
        with patch("gh_actions_optimizer.shared.cli.colors") as mock_colors:
            mock_console = Mock()
            mock_colors.get_console.return_value = mock_console
            
            cmd_security(args)
            
            # Verify the analysis detected multiple issues
            # The workflow should trigger several security checks
            mock_console.print.assert_called()

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.github.get_workflows")
    def test_cmd_security_exception_handling(self, mock_get_workflows, mock_validate_auth, mock_get_repo):
        """Test security command exception handling."""
        args = Mock(quiet=False, sample_data=False, format="table", output=None)
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = True
        
        # Simulate an exception during workflow analysis
        mock_get_workflows.side_effect = Exception("API Error")
        
        with patch("gh_actions_optimizer.shared.data.generate_sample_security_issues") as mock_sample_data:
            mock_sample_data.return_value = []
            
            with patch("gh_actions_optimizer.shared.cli.colors") as mock_colors:
                mock_console = Mock()
                mock_colors.get_console.return_value = mock_console
                
                cmd_security(args)
                
                # Should fallback to sample data on exception
                mock_sample_data.assert_called_once()

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.data.generate_sample_security_issues")
    def test_cmd_security_quiet_mode(self, mock_sample_data, mock_validate_auth, mock_get_repo):
        """Test security command in quiet mode."""
        args = Mock(quiet=True, sample_data=True, format="table", output=None)
        mock_get_repo.return_value = "sample/repo"
        mock_validate_auth.return_value = True
        mock_sample_data.return_value = []
        
        with patch("gh_actions_optimizer.shared.cli.colors") as mock_colors:
            mock_console = Mock()
            mock_colors.get_console.return_value = mock_console
            
            cmd_security(args)
            
            # In quiet mode, should still produce output but no initial info message
            mock_console.print.assert_called()

    @patch("gh_actions_optimizer.shared.github.get_repo_for_command")
    @patch("gh_actions_optimizer.shared.github.validate_github_auth")
    @patch("gh_actions_optimizer.shared.github.get_workflows")
    @patch("gh_actions_optimizer.shared.github.download_workflow_content")
    def test_cmd_security_no_issues_found(self, mock_download, mock_get_workflows, mock_validate_auth, mock_get_repo):
        """Test security command when no issues are found."""
        args = Mock(quiet=False, sample_data=False, format="table", output=None)
        mock_get_repo.return_value = "owner/repo"
        mock_validate_auth.return_value = True
        
        mock_get_workflows.return_value = [
            {
                "name": "secure.yml",
                "download_url": "https://example.com/secure.yml"
            }
        ]
        
        # Secure workflow content
        workflow_content = """
name: Secure Workflow
on: [push]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Secure workflow"
"""
        mock_download.return_value = workflow_content
        
        with patch("gh_actions_optimizer.shared.cli.colors") as mock_colors:
            mock_console = Mock()
            mock_colors.get_console.return_value = mock_console
            
            cmd_security(args)
            
            # Should display "No security issues found!" message
            print_calls = [call[0][0] for call in mock_console.print.call_args_list]
            assert any("No security issues found!" in str(call) for call in print_calls)