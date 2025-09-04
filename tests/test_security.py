"""Tests for security utilities."""

import pytest

from gh_actions_optimizer.shared.security import (
    SecuritySanitizer,
    mask_repository_url,
    sanitize_error_message,
    sanitize_for_logging,
    sanitize_subprocess_output,
    validate_github_token_format,
)


class TestSecuritySanitizer:
    """Test security sanitizer functionality."""

    def test_sanitize_github_tokens(self):
        """Test sanitization of GitHub tokens."""
        sanitizer = SecuritySanitizer()
        
        # Test different token formats
        test_cases = [
            "Token: ghp_1234567890abcdef1234567890abcdef12345678",
            "Bearer ghp_1234567890abcdef1234567890abcdef12345678",
            "Authorization: token ghp_1234567890abcdef1234567890abcdef12345678",
            "ghs_1234567890abcdef1234567890abcdef12345678",
            "ghu_1234567890abcdef1234567890abcdef12345678",
        ]
        
        for test_case in test_cases:
            result = sanitizer.sanitize_text(test_case)
            assert "[REDACTED]" in result
            assert "ghp_" not in result
            assert "ghs_" not in result
            assert "ghu_" not in result

    def test_sanitize_urls_with_credentials(self):
        """Test sanitization of URLs with embedded credentials."""
        sanitizer = SecuritySanitizer()
        
        test_cases = [
            "https://user:token@github.com/owner/repo",
            "https://github.com/owner/repo?token=abc123",
            "https://github.com/owner/repo?access_token=def456",
        ]
        
        for test_case in test_cases:
            result = sanitizer.sanitize_text(test_case)
            assert "[REDACTED]" in result
            assert "token@" not in result
            assert "token=abc123" not in result
            assert "access_token=def456" not in result

    def test_sanitize_dict_with_sensitive_keys(self):
        """Test sanitization of dictionaries with sensitive keys."""
        sanitizer = SecuritySanitizer()
        
        test_dict = {
            "username": "testuser",
            "password": "secret123",
            "github_token": "ghp_1234567890abcdef",
            "normal_key": "normal_value",
            "nested": {
                "api_key": "sensitive_data",
                "public_info": "safe_data"
            }
        }
        
        result = sanitizer.sanitize_dict(test_dict)
        
        assert result["username"] == "testuser"  # Not sensitive
        assert result["password"] == "[REDACTED]"
        assert result["github_token"] == "[REDACTED]"
        assert result["normal_key"] == "normal_value"
        assert result["nested"]["api_key"] == "[REDACTED]"
        assert result["nested"]["public_info"] == "safe_data"


class TestValidateGithubToken:
    """Test GitHub token validation."""

    def test_valid_token_formats(self):
        """Test validation of valid GitHub token formats."""
        valid_tokens = [
            "ghp_1234567890abcdef1234567890abcdef12345678",
            "ghs_1234567890abcdef1234567890abcdef12345678",
            "ghu_1234567890abcdef1234567890abcdef12345678",
            "1234567890abcdef1234567890abcdef12345678",  # Classic 40-char hex
        ]
        
        for token in valid_tokens:
            assert validate_github_token_format(token)

    def test_invalid_token_formats(self):
        """Test validation of invalid GitHub token formats."""
        invalid_tokens = [
            "",
            "short",
            "ghp_short",
            "not_a_token_format",
            "1234567890abcdefg",  # Invalid hex character
        ]
        
        for token in invalid_tokens:
            assert not validate_github_token_format(token)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_mask_repository_url(self):
        """Test URL masking functionality."""
        test_cases = [
            ("https://user:pass@github.com/owner/repo", "https://[REDACTED]@github.com/owner/repo"),
            ("https://github.com/owner/repo?token=abc123", "https://github.com/owner/repo?token=[REDACTED]"),
            ("https://github.com/owner/repo", "https://github.com/owner/repo"),  # No change needed
        ]
        
        for input_url, expected in test_cases:
            result = mask_repository_url(input_url)
            assert result == expected

    def test_sanitize_for_logging(self):
        """Test logging sanitization."""
        message = "Token: ghp_1234567890abcdef1234567890abcdef12345678"
        result = sanitize_for_logging(message)
        assert "ghp_" not in result
        assert "[REDACTED]" in result

    def test_sanitize_error_message(self):
        """Test error message sanitization."""
        error = "Authentication failed with token: ghp_1234567890abcdef1234567890abcdef12345678"
        result = sanitize_error_message(error)
        assert "ghp_" not in result
        assert "[REDACTED]" in result

    def test_sanitize_subprocess_output(self):
        """Test subprocess output sanitization."""
        output = "user: john\ntoken: ghp_1234567890abcdef"
        command_args = ["gh", "auth", "status"]
        
        result = sanitize_subprocess_output(output, command_args)
        assert "ghp_" not in result
        assert "[REDACTED]" in result