"""Tests for GitHub utilities."""

import json
import os
import subprocess
import urllib.error
from unittest.mock import Mock, patch, MagicMock
import pytest

from gh_actions_optimizer.shared.github import (
    get_current_repo,
    validate_repo,
    get_repo_for_command,
    run_gh_command,
    get_workflows,
    download_workflow_content,
    validate_github_auth,
    get_github_token_scopes,
)


class TestGetCurrentRepo:
    """Test get_current_repo function."""

    def test_get_current_repo_from_github_actions_env(self):
        """Test getting repo from GitHub Actions environment."""
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"}):
            result = get_current_repo()
            assert result == "owner/repo"

    @patch("subprocess.run")
    def test_get_current_repo_from_gh_cli(self, mock_run):
        """Test getting repo from gh CLI."""
        mock_result = Mock()
        mock_result.stdout = '{"nameWithOwner": "owner/repo"}'
        mock_run.return_value = mock_result
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_current_repo()
            assert result == "owner/repo"

    @patch("subprocess.run")
    def test_get_current_repo_from_git_remote(self, mock_run):
        """Test getting repo from git remote when gh fails."""
        # First call (gh) fails, second call (git) succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "gh"),
            Mock(stdout="https://github.com/owner/repo.git\n")
        ]
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_current_repo()
            assert result == "owner/repo"

    @patch("subprocess.run")
    def test_get_current_repo_git_remote_without_git_suffix(self, mock_run):
        """Test getting repo from git remote URL without .git suffix."""
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "gh"),
            Mock(stdout="https://github.com/owner/repo\n")
        ]
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_current_repo()
            assert result == "owner/repo"

    @patch("subprocess.run")
    def test_get_current_repo_all_methods_fail(self, mock_run):
        """Test when all methods to get repo fail."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_current_repo()
            assert result is None

    @patch("subprocess.run")
    def test_get_current_repo_gh_json_decode_error(self, mock_run):
        """Test when gh CLI returns invalid JSON."""
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result
        
        with patch.dict(os.environ, {}, clear=True):
            result = get_current_repo()
            assert result is None


class TestValidateRepo:
    """Test validate_repo function."""

    def test_validate_repo_valid_format(self):
        """Test validation of valid repo format."""
        result = validate_repo("owner/repo")
        assert result == "owner/repo"

    @patch("gh_actions_optimizer.shared.github.get_current_repo")
    @patch("sys.exit")
    def test_validate_repo_none_input_no_current_repo(self, mock_exit, mock_get_current):
        """Test validation when no repo provided and can't detect current."""
        mock_get_current.return_value = None
        mock_exit.side_effect = SystemExit(1)  # Actually exit
        
        with pytest.raises(SystemExit):
            validate_repo(None)
        mock_exit.assert_called_once_with(1)

    @patch("gh_actions_optimizer.shared.github.get_current_repo")
    def test_validate_repo_none_input_with_current_repo(self, mock_get_current):
        """Test validation when no repo provided but can detect current."""
        mock_get_current.return_value = "current/repo"
        
        result = validate_repo(None)
        assert result == "current/repo"

    @patch("sys.exit")
    def test_validate_repo_invalid_format_no_slash(self, mock_exit):
        """Test validation of invalid repo format without slash."""
        mock_exit.side_effect = SystemExit(1)  # Actually exit
        
        with pytest.raises(SystemExit):
            validate_repo("invalidformat")
        mock_exit.assert_called_with(1)

    @patch("sys.exit") 
    def test_validate_repo_invalid_format_empty_owner(self, mock_exit):
        """Test validation of invalid repo format with empty owner."""
        mock_exit.side_effect = SystemExit(1)  # Actually exit
        
        with pytest.raises(SystemExit):
            validate_repo("/repo")
        mock_exit.assert_called_with(1)

    @patch("sys.exit")
    def test_validate_repo_invalid_format_empty_repo(self, mock_exit):
        """Test validation of invalid repo format with empty repo."""
        mock_exit.side_effect = SystemExit(1)  # Actually exit
        
        with pytest.raises(SystemExit):
            validate_repo("owner/")
        mock_exit.assert_called_with(1)

    @patch("sys.exit")
    def test_validate_repo_invalid_format_too_many_parts(self, mock_exit):
        """Test validation of invalid repo format with too many parts."""
        mock_exit.side_effect = SystemExit(1)  # Actually exit
        
        with pytest.raises(SystemExit):
            validate_repo("owner/repo/extra")
        mock_exit.assert_called_with(1)


class TestGetRepoForCommand:
    """Test get_repo_for_command function."""

    def test_get_repo_for_command_sample_data(self):
        """Test getting repo when sample_data is True."""
        args = Mock(sample_data=True)
        result = get_repo_for_command(args)
        assert result == "sample/repo"

    @patch("gh_actions_optimizer.shared.github.validate_repo")
    def test_get_repo_for_command_with_repo_arg(self, mock_validate):
        """Test getting repo when repo argument is provided."""
        args = Mock(sample_data=False, repo="owner/repo")
        mock_validate.return_value = "owner/repo"
        
        result = get_repo_for_command(args)
        assert result == "owner/repo"

    @patch("gh_actions_optimizer.shared.github.get_current_repo")
    @patch("gh_actions_optimizer.shared.github.validate_repo")
    def test_get_repo_for_command_auto_detect(self, mock_validate, mock_get_current):
        """Test getting repo when auto-detecting."""
        args = Mock(sample_data=False, repo=None)
        mock_get_current.return_value = "detected/repo"
        mock_validate.return_value = "detected/repo"
        
        result = get_repo_for_command(args)
        assert result == "detected/repo"

    @patch("gh_actions_optimizer.shared.github.get_current_repo")
    @patch("sys.exit")
    def test_get_repo_for_command_auto_detect_fails(self, mock_exit, mock_get_current):
        """Test getting repo when auto-detection fails."""
        args = Mock(sample_data=False, repo=None)
        mock_get_current.return_value = None
        mock_exit.side_effect = SystemExit(1)  # Actually exit
        
        with pytest.raises(SystemExit):
            get_repo_for_command(args)
        mock_exit.assert_called_with(1)


class TestRunGhCommand:
    """Test run_gh_command function."""

    @patch("subprocess.run")
    def test_run_gh_command_success(self, mock_run):
        """Test successful gh command execution."""
        mock_result = Mock()
        mock_run.return_value = mock_result
        
        result = run_gh_command(["api", "user"])
        assert result == mock_result
        mock_run.assert_called_once_with(
            ["gh", "api", "user"], capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    @patch("sys.exit")
    def test_run_gh_command_failure(self, mock_exit, mock_run):
        """Test gh command execution failure."""
        error = subprocess.CalledProcessError(1, "gh")
        error.stderr = "Authentication failed"
        mock_run.side_effect = error
        
        run_gh_command(["api", "user"])
        mock_exit.assert_called_once_with(1)

    @patch("subprocess.run")
    def test_run_gh_command_no_check(self, mock_run):
        """Test gh command execution without check."""
        mock_result = Mock()
        mock_run.return_value = mock_result
        
        result = run_gh_command(["api", "user"], check=False)
        assert result == mock_result
        mock_run.assert_called_once_with(
            ["gh", "api", "user"], capture_output=True, text=True, check=False
        )


class TestGetWorkflows:
    """Test get_workflows function."""

    @patch("gh_actions_optimizer.shared.github.run_gh_command")
    def test_get_workflows_success(self, mock_run_gh):
        """Test successful workflow retrieval."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"name": "test.yml", "type": "file"}\n{"name": "ci.yml", "type": "file"}'
        mock_run_gh.return_value = mock_result
        
        result = get_workflows("owner/repo")
        assert len(result) == 2
        assert result[0]["name"] == "test.yml"
        assert result[1]["name"] == "ci.yml"

    @patch("gh_actions_optimizer.shared.github.run_gh_command")
    def test_get_workflows_failure(self, mock_run_gh):
        """Test workflow retrieval failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run_gh.return_value = mock_result
        
        result = get_workflows("owner/repo")
        assert result == []

    @patch("gh_actions_optimizer.shared.github.run_gh_command")
    def test_get_workflows_invalid_json(self, mock_run_gh):
        """Test workflow retrieval with invalid JSON."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'invalid json\n{"name": "valid.yml", "type": "file"}'
        mock_run_gh.return_value = mock_result
        
        result = get_workflows("owner/repo")
        assert len(result) == 1
        assert result[0]["name"] == "valid.yml"


class TestDownloadWorkflowContent:
    """Test download_workflow_content function."""

    @patch("urllib.request.urlopen")
    def test_download_workflow_content_success(self, mock_urlopen):
        """Test successful workflow content download."""
        mock_response = Mock()
        mock_response.read.return_value = b"workflow content"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = download_workflow_content("https://example.com/workflow.yml")
        assert result == "workflow content"

    @patch("urllib.request.urlopen")
    def test_download_workflow_content_url_error(self, mock_urlopen):
        """Test workflow content download with URL error."""
        mock_urlopen.side_effect = urllib.error.URLError("Network error")
        
        result = download_workflow_content("https://example.com/workflow.yml")
        assert result == ""

    @patch("urllib.request.urlopen")
    def test_download_workflow_content_unicode_error(self, mock_urlopen):
        """Test workflow content download with Unicode decode error."""
        mock_response = Mock()
        mock_response.read.return_value = b"\xff\xfe"  # Invalid UTF-8
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = download_workflow_content("https://example.com/workflow.yml")
        assert result == ""


class TestValidateGithubAuth:
    """Test validate_github_auth function."""

    @patch("subprocess.run")
    def test_validate_github_auth_success(self, mock_run):
        """Test successful GitHub authentication validation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = validate_github_auth()
        assert result is True

    @patch("subprocess.run")
    def test_validate_github_auth_failure(self, mock_run):
        """Test failed GitHub authentication validation."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = validate_github_auth()
        assert result is False

    @patch("subprocess.run")
    def test_validate_github_auth_subprocess_error(self, mock_run):
        """Test GitHub authentication validation with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
        
        result = validate_github_auth()
        assert result is False

    @patch("subprocess.run")
    def test_validate_github_auth_file_not_found(self, mock_run):
        """Test GitHub authentication validation when gh CLI not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = validate_github_auth()
        assert result is False


class TestGetGithubTokenScopes:
    """Test get_github_token_scopes function."""

    @patch("subprocess.run")
    def test_get_github_token_scopes_success(self, mock_run):
        """Test successful token scopes retrieval."""
        # First call returns token, second call returns scopes
        mock_run.side_effect = [
            Mock(stdout="ghp_token123\n"),
            Mock(returncode=0, stderr="x-oauth-scopes: repo, user\n")
        ]
        
        result = get_github_token_scopes()
        assert result == ["repo", "user"]

    @patch("subprocess.run")
    def test_get_github_token_scopes_no_scopes(self, mock_run):
        """Test token scopes retrieval with no scopes."""
        mock_run.side_effect = [
            Mock(stdout="ghp_token123\n"),
            Mock(returncode=0, stderr="x-oauth-scopes: \n")
        ]
        
        result = get_github_token_scopes()
        assert result == []

    @patch("subprocess.run")
    def test_get_github_token_scopes_api_failure(self, mock_run):
        """Test token scopes retrieval when API call fails."""
        mock_run.side_effect = [
            Mock(stdout="ghp_token123\n"),
            Mock(returncode=1, stderr="API call failed\n")
        ]
        
        result = get_github_token_scopes()
        assert result == []

    @patch("subprocess.run")
    def test_get_github_token_scopes_subprocess_error(self, mock_run):
        """Test token scopes retrieval with subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
        
        result = get_github_token_scopes()
        assert result == []

    @patch("subprocess.run")
    def test_get_github_token_scopes_file_not_found(self, mock_run):
        """Test token scopes retrieval when gh CLI not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = get_github_token_scopes()
        assert result == []

    @patch("subprocess.run")
    def test_get_github_token_scopes_no_token(self, mock_run):
        """Test token scopes retrieval when no token available."""
        mock_run.return_value = Mock(stdout="\n")
        
        result = get_github_token_scopes()
        assert result == []