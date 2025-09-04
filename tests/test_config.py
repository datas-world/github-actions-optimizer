"""Tests for configuration utilities."""

import os
from unittest.mock import patch, Mock
import pytest

from gh_actions_optimizer.shared.config import (
    SecureConfig,
    secure_config,
    get_github_token,
    validate_configuration,
)


class TestSecureConfig:
    """Test SecureConfig class functionality."""

    def test_init(self):
        """Test SecureConfig initialization."""
        config = SecureConfig()
        assert config._config == {}

    @patch("gh_actions_optimizer.shared.config.get_secure_env_var")
    def test_get_github_token_found_github_token(self, mock_get_env):
        """Test getting GitHub token from GITHUB_TOKEN env var."""
        mock_get_env.side_effect = lambda var: "test_token" if var == "GITHUB_TOKEN" else None
        
        config = SecureConfig()
        result = config.get_github_token()
        assert result == "test_token"

    @patch("gh_actions_optimizer.shared.config.get_secure_env_var")
    def test_get_github_token_found_gh_token(self, mock_get_env):
        """Test getting GitHub token from GH_TOKEN env var."""
        mock_get_env.side_effect = lambda var: "test_token" if var == "GH_TOKEN" else None
        
        config = SecureConfig()
        result = config.get_github_token()
        assert result == "test_token"

    @patch("gh_actions_optimizer.shared.config.get_secure_env_var")
    def test_get_github_token_found_github_access_token(self, mock_get_env):
        """Test getting GitHub token from GITHUB_ACCESS_TOKEN env var."""
        mock_get_env.side_effect = lambda var: "test_token" if var == "GITHUB_ACCESS_TOKEN" else None
        
        config = SecureConfig()
        result = config.get_github_token()
        assert result == "test_token"

    @patch("gh_actions_optimizer.shared.config.get_secure_env_var")
    def test_get_github_token_not_found(self, mock_get_env):
        """Test getting GitHub token when none found."""
        mock_get_env.return_value = None
        
        config = SecureConfig()
        result = config.get_github_token()
        assert result is None

    def test_get_config_value_from_env_upper(self):
        """Test getting config value from environment (uppercase)."""
        config = SecureConfig()
        
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
            result = config.get_config_value("test_key")
            assert result == "test_value"

    def test_get_config_value_from_env_exact(self):
        """Test getting config value from environment (exact case)."""
        config = SecureConfig()
        
        with patch.dict(os.environ, {"test_key": "test_value"}):
            result = config.get_config_value("test_key")
            assert result == "test_value"

    def test_get_config_value_from_internal_config(self):
        """Test getting config value from internal config."""
        config = SecureConfig()
        config._config["test_key"] = "internal_value"
        
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_config_value("test_key")
            assert result == "internal_value"

    def test_get_config_value_default(self):
        """Test getting config value with default."""
        config = SecureConfig()
        
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_config_value("nonexistent_key", "default_value")
            assert result == "default_value"

    def test_set_config_value(self):
        """Test setting config value."""
        config = SecureConfig()
        config.set_config_value("test_key", "test_value")
        assert config._config["test_key"] == "test_value"

    @patch.object(SecureConfig, "get_github_token")
    def test_validate_required_config_with_token(self, mock_get_token):
        """Test validation when GitHub token is available."""
        mock_get_token.return_value = "test_token"
        
        config = SecureConfig()
        result = config.validate_required_config()
        assert result is True

    @patch.object(SecureConfig, "get_github_token")
    def test_validate_required_config_without_token(self, mock_get_token):
        """Test validation when GitHub token is not available."""
        mock_get_token.return_value = None
        
        config = SecureConfig()
        result = config.validate_required_config()
        assert result is False

    def test_get_safe_config_summary_all_set(self):
        """Test getting safe config summary with all env vars set."""
        env_vars = {
            "GITHUB_TOKEN": "token",
            "GH_TOKEN": "token", 
            "GITHUB_ACCESS_TOKEN": "token",
            "GITHUB_REPOSITORY": "repo",
            "GITHUB_ACTOR": "actor",
            "GITHUB_WORKFLOW": "workflow",
        }
        
        config = SecureConfig()
        
        with patch.dict(os.environ, env_vars):
            result = config.get_safe_config_summary()
            
            for var in env_vars.keys():
                assert result[var] == "SET"

    def test_get_safe_config_summary_none_set(self):
        """Test getting safe config summary with no env vars set."""
        config = SecureConfig()
        
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_safe_config_summary()
            
            expected_vars = [
                "GITHUB_TOKEN",
                "GH_TOKEN", 
                "GITHUB_ACCESS_TOKEN",
                "GITHUB_REPOSITORY",
                "GITHUB_ACTOR",
                "GITHUB_WORKFLOW",
            ]
            
            for var in expected_vars:
                assert result[var] == "NOT_SET"

    def test_get_safe_config_summary_partial_set(self):
        """Test getting safe config summary with some env vars set."""
        config = SecureConfig()
        
        with patch.dict(os.environ, {"GITHUB_TOKEN": "token", "GITHUB_REPOSITORY": "repo"}, clear=True):
            result = config.get_safe_config_summary()
            
            assert result["GITHUB_TOKEN"] == "SET"
            assert result["GITHUB_REPOSITORY"] == "SET"
            assert result["GH_TOKEN"] == "NOT_SET"
            assert result["GITHUB_ACCESS_TOKEN"] == "NOT_SET"
            assert result["GITHUB_ACTOR"] == "NOT_SET"
            assert result["GITHUB_WORKFLOW"] == "NOT_SET"


class TestGlobalFunctions:
    """Test global configuration functions."""

    @patch.object(secure_config, "get_github_token")
    def test_get_github_token_function(self, mock_method):
        """Test global get_github_token function."""
        mock_method.return_value = "test_token"
        
        result = get_github_token()
        assert result == "test_token"
        mock_method.assert_called_once()

    @patch.object(secure_config, "validate_required_config")
    def test_validate_configuration_function(self, mock_method):
        """Test global validate_configuration function."""
        mock_method.return_value = True
        
        result = validate_configuration()
        assert result is True
        mock_method.assert_called_once()