"""Tests for GitHub module validation integration."""

import json
import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from gh_actions_optimizer.shared.github import get_current_repo
from gh_actions_optimizer.shared.validation import ValidationError


class TestGetCurrentRepo:
    """Test cases for get_current_repo function."""

    def test_github_actions_env_valid(self) -> None:
        """Test valid GitHub Actions environment variable."""
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"}):
            result = get_current_repo()
            assert result == "owner/repo"

    def test_github_actions_env_invalid(self) -> None:
        """Test invalid GitHub Actions environment variable falls back."""
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "../malicious"}):
            # Mock subprocess to avoid actually calling gh CLI
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
                result = get_current_repo()
                # Should fall back and ultimately return None since gh CLI fails
                assert result is None

    def test_github_actions_env_missing(self) -> None:
        """Test behavior when GitHub Actions env var is missing."""
        # Ensure the env var is not set
        with patch.dict(os.environ, {}, clear=True):
            # Mock subprocess to avoid actually calling gh CLI
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
                result = get_current_repo()
                # Should return None since both env var and gh CLI fail
                assert result is None

    def test_gh_cli_success(self) -> None:
        """Test successful gh CLI detection."""
        # Mock successful gh CLI response
        mock_result = MagicMock()
        mock_result.stdout = '{"nameWithOwner": "owner/repo"}'
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run', return_value=mock_result) as mock_run:
                result = get_current_repo()
                assert result == "owner/repo"
                mock_run.assert_called_once()

    def test_gh_cli_invalid_json(self) -> None:
        """Test gh CLI with invalid JSON response."""
        mock_result = MagicMock()
        mock_result.stdout = 'invalid json'
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run', return_value=mock_result):
                result = get_current_repo()
                # Should handle JSON decode error and return None
                assert result is None

    def test_gh_cli_missing_field(self) -> None:
        """Test gh CLI with missing nameWithOwner field."""
        mock_result = MagicMock()
        mock_result.stdout = '{"otherField": "value"}'
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run', return_value=mock_result):
                result = get_current_repo()
                # Should handle missing field and return None
                assert result is None

    def test_gh_cli_non_string_field(self) -> None:
        """Test gh CLI with non-string nameWithOwner field."""
        mock_result = MagicMock()
        mock_result.stdout = '{"nameWithOwner": 123}'
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run', return_value=mock_result):
                result = get_current_repo()
                # Should handle non-string field and return None
                assert result is None

    def test_gh_cli_command_error(self) -> None:
        """Test gh CLI command failure."""
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
                result = get_current_repo()
                # Should handle command error and return None
                assert result is None

    def test_gh_cli_file_not_found(self) -> None:
        """Test gh CLI not installed."""
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run') as mock_run:
                # First call (gh) raises FileNotFoundError, second call (git) also fails
                mock_run.side_effect = [
                    FileNotFoundError("gh not found"),
                    subprocess.CalledProcessError(1, "git")
                ]
                result = get_current_repo()
                # Should handle missing gh command and return None
                assert result is None

    def test_git_fallback_success(self) -> None:
        """Test successful git remote fallback."""
        mock_git_result = MagicMock()
        mock_git_result.stdout = "https://github.com/owner/repo.git"
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run') as mock_run:
                # First call (gh) fails, second call (git) succeeds
                mock_run.side_effect = [
                    subprocess.CalledProcessError(1, "gh"),
                    mock_git_result
                ]
                result = get_current_repo()
                assert result == "owner/repo"

    def test_git_fallback_invalid_url(self) -> None:
        """Test git remote fallback with invalid URL."""
        mock_git_result = MagicMock()
        mock_git_result.stdout = "not-a-github-url"
        
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run') as mock_run:
                # First call (gh) fails, second call (git) returns invalid URL
                mock_run.side_effect = [
                    subprocess.CalledProcessError(1, "gh"),
                    mock_git_result
                ]
                result = get_current_repo()
                # Should handle invalid URL and return None
                assert result is None

    def test_git_fallback_command_error(self) -> None:
        """Test git remote fallback command failure."""
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run') as mock_run:
                # Both gh and git commands fail
                mock_run.side_effect = [
                    subprocess.CalledProcessError(1, "gh"),
                    subprocess.CalledProcessError(1, "git")
                ]
                result = get_current_repo()
                # Should return None when all methods fail
                assert result is None

    def test_all_methods_fail(self) -> None:
        """Test when all detection methods fail."""
        with patch.dict(os.environ, {}, clear=True):  # No env var
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "command")
                result = get_current_repo()
                # Should return None when all methods fail
                assert result is None