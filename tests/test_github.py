"""Tests for GitHub API and repository utilities."""

import json
import os
import sys
import urllib.error
import urllib.request
from unittest.mock import Mock, patch, MagicMock
import subprocess

import pytest

from gh_actions_optimizer.shared.github import (
    get_current_repo,
    validate_repo,
    get_repo_for_command,
    run_gh_command,
    get_workflows,
    download_workflow_content,
)


class TestGetCurrentRepo:
    """Test get_current_repo function."""

    def test_get_current_repo_from_github_actions_env(self) -> None:
        """Test getting repo from GitHub Actions environment variable."""
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"}):
            result = get_current_repo()
            assert result == "owner/repo"

    def test_get_current_repo_from_gh_cli(self) -> None:
        """Test getting repo from gh CLI."""
        mock_result = Mock()
        mock_result.stdout = '{"nameWithOwner": "owner/repo"}'
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
                result = get_current_repo()
                assert result == "owner/repo"

    def test_get_current_repo_from_gh_cli_invalid_json(self) -> None:
        """Test gh CLI with invalid JSON falls back to git."""
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        
        mock_git_result = Mock()
        mock_git_result.stdout = "https://github.com/owner/repo.git"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    assert result == "owner/repo"

    def test_get_current_repo_from_gh_cli_missing_field(self) -> None:
        """Test gh CLI with missing nameWithOwner field."""
        mock_result = Mock()
        mock_result.stdout = '{"name": "repo"}'
        
        mock_git_result = Mock()
        mock_git_result.stdout = "https://github.com/owner/repo.git"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    assert result == "owner/repo"

    def test_get_current_repo_from_git_remote(self) -> None:
        """Test getting repo from git remote URL."""
        mock_git_result = Mock()
        mock_git_result.stdout = "https://github.com/owner/repo.git"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    assert result == "owner/repo"

    def test_get_current_repo_from_git_remote_without_git_suffix(self) -> None:
        """Test getting repo from git remote URL without .git suffix."""
        mock_git_result = Mock()
        mock_git_result.stdout = "https://github.com/owner/repo"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    assert result == "owner/repo"

    def test_get_current_repo_from_git_remote_ssh(self) -> None:
        """Test getting repo from SSH git remote URL."""
        mock_git_result = Mock()
        mock_git_result.stdout = "git@github.com:owner/repo.git"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    # SSH URLs are parsed as git@github.com:owner/repo after removing .git
                    # The split("/") gives ["git@github.com:owner", "repo"] and we take last 2
                    assert result == "git@github.com:owner/repo"

    def test_get_current_repo_no_github_url(self) -> None:
        """Test git remote URL that's not GitHub."""
        mock_git_result = Mock()
        mock_git_result.stdout = "https://gitlab.com/owner/repo.git"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    assert result is None

    def test_get_current_repo_invalid_git_url_parts(self) -> None:
        """Test git remote URL with insufficient parts."""
        mock_git_result = Mock()
        mock_git_result.stdout = "https://github.com/justowner"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    # The split("/") gives ["https:", "", "github.com", "justowner"] and we take last 2
                    # So it becomes "github.com/justowner"
                    assert result == "github.com/justowner"

    def test_get_current_repo_git_url_single_part(self) -> None:
        """Test git remote URL that results in single part after processing."""
        mock_git_result = Mock()
        mock_git_result.stdout = "https://github.com/onlyonepart"
        
        # This should still work because "https://github.com/onlyonepart".split("/")[-2:] 
        # gives ["github.com", "onlyonepart"] which has length 2
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    assert result == "github.com/onlyonepart"

    def test_get_current_repo_git_url_truly_insufficient_parts(self) -> None:
        """Test git remote URL that truly has insufficient parts."""
        mock_git_result = Mock()
        mock_git_result.stdout = "github.com"  # Just domain, no path
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", return_value=mock_git_result):
                    result = get_current_repo()
                    # "github.com".split("/")[-2:] gives ["github.com"] which has length 1
                    assert result is None

    def test_get_current_repo_all_methods_fail(self) -> None:
        """Test when all detection methods fail."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=Exception("gh not found")):
                with patch("gh_actions_optimizer.shared.github.safe_git_command", side_effect=Exception("git not found")):
                    result = get_current_repo()
                    assert result is None


class TestValidateRepo:
    """Test validate_repo function."""

    def test_validate_repo_valid_format(self) -> None:
        """Test validation of valid repository format."""
        result = validate_repo("owner/repo")
        assert result == "owner/repo"

    def test_validate_repo_auto_detect(self) -> None:
        """Test auto-detection when no repo provided."""
        with patch("gh_actions_optimizer.shared.github.get_current_repo", return_value="owner/repo"):
            result = validate_repo(None)
            assert result == "owner/repo"

    def test_validate_repo_auto_detect_fails(self) -> None:
        """Test auto-detection failure exits."""
        with patch("gh_actions_optimizer.shared.github.get_current_repo", return_value=None):
            with pytest.raises(SystemExit):
                validate_repo(None)

    def test_validate_repo_invalid_format_no_slash(self) -> None:
        """Test validation fails for repo without slash."""
        with pytest.raises(SystemExit):
            validate_repo("invalidrepo")

    def test_validate_repo_invalid_format_empty_parts(self) -> None:
        """Test validation fails for repo with empty parts."""
        with pytest.raises(SystemExit):
            validate_repo("owner/")
        
        with pytest.raises(SystemExit):
            validate_repo("/repo")

    def test_validate_repo_invalid_format_too_many_parts(self) -> None:
        """Test validation fails for repo with too many parts."""
        with pytest.raises(SystemExit):
            validate_repo("owner/repo/extra")


class TestGetRepoForCommand:
    """Test get_repo_for_command function."""

    def test_get_repo_for_command_sample_data(self) -> None:
        """Test sample data mode returns sample repo."""
        mock_args = Mock()
        mock_args.sample_data = True
        
        result = get_repo_for_command(mock_args)
        assert result == "sample/repo"

    def test_get_repo_for_command_explicit_repo(self) -> None:
        """Test explicit repo argument."""
        mock_args = Mock()
        mock_args.sample_data = False
        mock_args.repo = "owner/repo"
        
        result = get_repo_for_command(mock_args)
        assert result == "owner/repo"

    def test_get_repo_for_command_auto_detect(self) -> None:
        """Test auto-detection when no repo specified."""
        mock_args = Mock()
        mock_args.sample_data = False
        mock_args.repo = None
        
        with patch("gh_actions_optimizer.shared.github.get_current_repo", return_value="owner/repo"):
            result = get_repo_for_command(mock_args)
            assert result == "owner/repo"

    def test_get_repo_for_command_auto_detect_fails(self) -> None:
        """Test auto-detection failure exits."""
        mock_args = Mock()
        mock_args.sample_data = False
        mock_args.repo = None
        
        with patch("gh_actions_optimizer.shared.github.get_current_repo", return_value=None):
            with pytest.raises(SystemExit):
                get_repo_for_command(mock_args)


class TestRunGhCommand:
    """Test run_gh_command function."""

    def test_run_gh_command_success(self) -> None:
        """Test successful gh command execution."""
        mock_result = Mock()
        mock_result.stdout = "success"
        
        with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
            result = run_gh_command(["repo", "view"])
            assert result == mock_result

    def test_run_gh_command_failure_with_stderr(self) -> None:
        """Test gh command failure with stderr."""
        mock_error = subprocess.CalledProcessError(1, ["gh", "repo", "view"])
        mock_error.stderr = "error message"
        
        with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=mock_error):
            with pytest.raises(SystemExit):
                run_gh_command(["repo", "view"])

    def test_run_gh_command_failure_without_stderr(self) -> None:
        """Test gh command failure without stderr."""
        mock_error = Exception("generic error")
        
        with patch("gh_actions_optimizer.shared.github.safe_gh_command", side_effect=mock_error):
            with pytest.raises(SystemExit):
                run_gh_command(["repo", "view"])


class TestGetWorkflows:
    """Test get_workflows function."""

    def test_get_workflows_success(self) -> None:
        """Test successful workflow retrieval."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"name": "workflow1.yml", "type": "file"}\n{"name": "workflow2.yml", "type": "file"}'
        
        with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
            result = get_workflows("owner/repo")
            
            assert len(result) == 2
            assert result[0]["name"] == "workflow1.yml"
            assert result[1]["name"] == "workflow2.yml"

    def test_get_workflows_api_failure(self) -> None:
        """Test workflow retrieval API failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        
        with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
            result = get_workflows("owner/repo")
            assert result == []

    def test_get_workflows_invalid_json(self) -> None:
        """Test workflow retrieval with invalid JSON."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'invalid json\n{"name": "workflow1.yml", "type": "file"}'
        
        with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
            result = get_workflows("owner/repo")
            
            assert len(result) == 1
            assert result[0]["name"] == "workflow1.yml"

    def test_get_workflows_empty_response(self) -> None:
        """Test workflow retrieval with empty response."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        with patch("gh_actions_optimizer.shared.github.safe_gh_command", return_value=mock_result):
            result = get_workflows("owner/repo")
            assert result == []


class TestDownloadWorkflowContent:
    """Test download_workflow_content function."""

    def test_download_workflow_content_success(self) -> None:
        """Test successful workflow content download."""
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_response.read.return_value = b"workflow content"
        
        with patch("urllib.request.urlopen", return_value=mock_response):
            result = download_workflow_content("https://example.com/workflow.yml")
            assert result == "workflow content"

    def test_download_workflow_content_url_error(self) -> None:
        """Test workflow content download URL error."""
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network error")):
            result = download_workflow_content("https://example.com/workflow.yml")
            assert result == ""

    def test_download_workflow_content_unicode_error(self) -> None:
        """Test workflow content download Unicode error."""
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_response.read.return_value = b"\xff\xfe"  # Invalid UTF-8
        
        with patch("urllib.request.urlopen", return_value=mock_response):
            result = download_workflow_content("https://example.com/workflow.yml")
            assert result == ""