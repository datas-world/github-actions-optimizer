"""Tests for input validation and sanitization."""

import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from gh_actions_optimizer.shared.validation import (
    InputValidator,
    ValidationError,
    validate_and_log_error,
)


class TestInputValidator:
    """Test cases for InputValidator class."""

    def test_validate_repository_name_valid(self) -> None:
        """Test valid repository names."""
        valid_repos = [
            "owner/repo",
            "my-org/my-repo",
            "user123/project_name",
            "a/b",
            "facebook/react",
            "microsoft/vscode",
        ]
        
        for repo in valid_repos:
            result = InputValidator.validate_repository_name(repo)
            assert result == repo

    def test_validate_repository_name_invalid(self) -> None:
        """Test invalid repository names."""
        invalid_repos = [
            "",
            "repo",  # Missing owner
            "/repo",  # Missing owner
            "owner/",  # Missing repo
            "owner//repo",  # Double slash
            "../owner/repo",  # Directory traversal
            "owner/repo/../evil",  # Directory traversal
            "owner/${injection}",  # Variable injection
            "owner/repo<script>",  # Script injection
            "a" * 101,  # Too long
        ]
        
        for repo in invalid_repos:
            with pytest.raises(ValidationError):
                InputValidator.validate_repository_name(repo)

    def test_validate_repository_name_none(self) -> None:
        """Test None repository name."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_repository_name(None)  # type: ignore

    def test_validate_file_path_valid(self) -> None:
        """Test valid file paths."""
        valid_paths = [
            "file.txt",
            "dir/file.txt",
            "path/to/file.yml",
            "/tmp/absolute.txt",  # When absolute allowed
        ]
        
        for path in valid_paths[:-1]:  # Test relative paths
            result = InputValidator.validate_file_path(path)
            assert result == os.path.normpath(path)
        
        # Test absolute path when allowed
        result = InputValidator.validate_file_path(valid_paths[-1], allow_absolute=True)
        assert result == os.path.normpath(valid_paths[-1])

    def test_validate_file_path_invalid(self) -> None:
        """Test invalid file paths."""
        invalid_paths = [
            "",
            "../../../etc/passwd",  # Directory traversal
            "path/with/../traversal",  # Directory traversal
            "${HOME}/file",  # Variable injection
            "file<script>",  # Script injection
            "\\\\server\\share",  # UNC path
            "/tmp/absolute.txt",  # Absolute when not allowed
        ]
        
        for path in invalid_paths[:-1]:  # Test all except last
            with pytest.raises(ValidationError):
                InputValidator.validate_file_path(path)
        
        # Test absolute path when not allowed
        with pytest.raises(ValidationError, match="Absolute paths not allowed"):
            InputValidator.validate_file_path(invalid_paths[-1], allow_absolute=False)

    def test_validate_filename_valid(self) -> None:
        """Test valid filenames."""
        valid_filenames = [
            "file.txt",
            "my-document.yml",
            "config_file.json",
            "123.txt",
            "file with spaces.txt",
        ]
        
        for filename in valid_filenames:
            result = InputValidator.validate_filename(filename)
            assert result == filename

    def test_validate_filename_invalid(self) -> None:
        """Test invalid filenames."""
        invalid_filenames = [
            "",
            "file\x00.txt",  # Null byte
            "file\x01.txt",  # Control character
            "CON.txt",  # Reserved Windows name
            "PRN.log",  # Reserved Windows name
            "file${injection}.txt",  # Variable injection
            "a" * 300,  # Too long
        ]
        
        for filename in invalid_filenames:
            with pytest.raises(ValidationError):
                InputValidator.validate_filename(filename)

    def test_validate_yaml_content_valid(self) -> None:
        """Test valid YAML content."""
        valid_yaml = """
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
        result = InputValidator.validate_yaml_content(valid_yaml)
        assert isinstance(result, dict)
        assert result["name"] == "CI"

    def test_validate_yaml_content_invalid(self) -> None:
        """Test invalid YAML content."""
        invalid_yamls = [
            "",
            "invalid: yaml: content: [",  # Invalid syntax
            "content: ${injection}",  # Variable injection
            "content: <script>alert('xss')</script>",  # Script injection
            "a" * (InputValidator.MAX_CONTENT_LENGTH + 1),  # Too large
        ]
        
        for yaml_content in invalid_yamls:
            with pytest.raises(ValidationError):
                InputValidator.validate_yaml_content(yaml_content)

    def test_validate_github_ref_valid(self) -> None:
        """Test valid GitHub references."""
        valid_refs = [
            "main",
            "feature-branch",
            "v1.0.0",
            "refs/heads/main",
            "feature/new-component",
        ]
        
        for ref in valid_refs:
            result = InputValidator.validate_github_ref(ref)
            assert result == ref

    def test_validate_github_ref_invalid(self) -> None:
        """Test invalid GitHub references."""
        invalid_refs = [
            "",
            "../malicious",  # Directory traversal
            "${injection}",  # Variable injection
            "ref with spaces",  # Spaces not allowed
            "ref<script>",  # Script injection
            "a" * 300,  # Too long
        ]
        
        for ref in invalid_refs:
            with pytest.raises(ValidationError):
                InputValidator.validate_github_ref(ref)

    def test_validate_commit_sha_valid(self) -> None:
        """Test valid commit SHAs."""
        valid_shas = [
            "a1b2c3d",  # Short SHA
            "a1b2c3d4e5f6789012345678901234567890abcd",  # Full SHA
            "ABCDEF0123456789",  # Uppercase (gets lowercased)
        ]
        
        for sha in valid_shas:
            result = InputValidator.validate_commit_sha(sha)
            assert result == sha.lower()

    def test_validate_commit_sha_invalid(self) -> None:
        """Test invalid commit SHAs."""
        invalid_shas = [
            "",
            "invalid",  # Non-hex characters
            "123",  # Too short
            "a1b2c3d4e5f6789012345678901234567890abcdef",  # Too long
            "../injection",  # Directory traversal
        ]
        
        for sha in invalid_shas:
            with pytest.raises(ValidationError):
                InputValidator.validate_commit_sha(sha)

    def test_validate_environment_variable_valid(self) -> None:
        """Test valid environment variables."""
        valid_vars = [
            ("HOME", "/home/user"),
            ("PATH", "/usr/bin:/bin"),
            ("MY_CUSTOM_VAR", "value123"),
            ("DEBUG", "true"),
        ]
        
        for name, value in valid_vars:
            result_name, result_value = InputValidator.validate_environment_variable(name, value)
            assert result_name == name
            assert result_value == value

    def test_validate_environment_variable_invalid(self) -> None:
        """Test invalid environment variables."""
        invalid_vars = [
            ("", "value"),  # Empty name
            ("123INVALID", "value"),  # Invalid name format
            ("my-var", "value"),  # Hyphens not allowed
            ("VALID_NAME", "${injection}"),  # Injection in value
            ("VALID_NAME", "a" * 5000),  # Value too long
        ]
        
        for name, value in invalid_vars:
            with pytest.raises(ValidationError):
                InputValidator.validate_environment_variable(name, value)

    def test_validate_url_valid(self) -> None:
        """Test valid URLs."""
        valid_urls = [
            "https://github.com/owner/repo",
            "http://example.com",
            "https://api.github.com/repos/owner/repo",
        ]
        
        for url in valid_urls:
            result = InputValidator.validate_url(url)
            assert result == url

    def test_validate_url_invalid(self) -> None:
        """Test invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://ftp.example.com",  # FTP not allowed by default
            "javascript:alert('xss')",  # Script injection
            "https://github.com/../injection",  # Directory traversal
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                InputValidator.validate_url(url)

    def test_validate_url_custom_schemes(self) -> None:
        """Test URL validation with custom allowed schemes."""
        result = InputValidator.validate_url("ftp://ftp.example.com", ["ftp"])
        assert result == "ftp://ftp.example.com"
        
        with pytest.raises(ValidationError):
            InputValidator.validate_url("http://example.com", ["https"])

    def test_validate_input_length_valid(self) -> None:
        """Test valid input length."""
        result = InputValidator.validate_input_length("test", 10, "Test input")
        assert result == "test"

    def test_validate_input_length_invalid(self) -> None:
        """Test invalid input length."""
        with pytest.raises(ValidationError, match="Test input too long"):
            InputValidator.validate_input_length("too long", 5, "Test input")

    def test_sanitize_for_shell_valid(self) -> None:
        """Test safe shell values."""
        safe_values = [
            "simple-value",
            "value123",
            "path/to/file",
            "value.with.dots",
        ]
        
        for value in safe_values:
            result = InputValidator.sanitize_for_shell(value)
            assert result == value

    def test_sanitize_for_shell_invalid(self) -> None:
        """Test unsafe shell values."""
        unsafe_values = [
            "value; rm -rf /",  # Command injection
            "value && malicious",  # Command chaining
            "value | cat /etc/passwd",  # Piping
            "value `echo hacked`",  # Command substitution
            "value $(malicious)",  # Command substitution
        ]
        
        for value in unsafe_values:
            with pytest.raises(ValidationError):
                InputValidator.sanitize_for_shell(value)

    def test_validate_file_extension_valid(self) -> None:
        """Test valid file extensions."""
        result = InputValidator.validate_file_extension("file.yml", [".yml", ".yaml"])
        assert result == "file.yml"
        
        result = InputValidator.validate_file_extension("FILE.YAML", [".yml", ".yaml"])
        assert result == "file.yaml"

    def test_validate_file_extension_invalid(self) -> None:
        """Test invalid file extensions."""
        with pytest.raises(ValidationError, match="File extension not allowed"):
            InputValidator.validate_file_extension("file.txt", [".yml", ".yaml"])

    def test_validate_file_size_valid(self) -> None:
        """Test valid file size."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("small content")
            tmp.flush()
            
            try:
                InputValidator.validate_file_size(tmp.name, 1000)  # Should not raise
            finally:
                os.unlink(tmp.name)

    def test_validate_file_size_invalid(self) -> None:
        """Test invalid file size."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("x" * 1000)
            tmp.flush()
            
            try:
                with pytest.raises(ValidationError, match="File too large"):
                    InputValidator.validate_file_size(tmp.name, 500)
            finally:
                os.unlink(tmp.name)

    def test_validate_file_size_nonexistent(self) -> None:
        """Test file size validation for nonexistent file."""
        with pytest.raises(ValidationError, match="File does not exist"):
            InputValidator.validate_file_size("/nonexistent/file", 1000)


class TestValidateAndLogError:
    """Test cases for validate_and_log_error helper function."""

    def test_valid_input(self) -> None:
        """Test valid input passes through."""
        result = validate_and_log_error(
            InputValidator.validate_repository_name, 
            "owner/repo"
        )
        assert result == "owner/repo"

    def test_invalid_input_exits(self) -> None:
        """Test invalid input causes system exit."""
        with pytest.raises(SystemExit):
            validate_and_log_error(
                InputValidator.validate_repository_name, 
                "invalid"
            )


class TestValidationIntegration:
    """Integration tests for validation in the broader context."""

    def test_yaml_workflow_validation(self) -> None:
        """Test validation of a realistic GitHub Actions workflow."""
        workflow_content = """
name: CI
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: pytest
"""
        
        result = InputValidator.validate_yaml_content(workflow_content)
        assert isinstance(result, dict)
        assert result["name"] == "CI"
        assert "jobs" in result
        assert "test" in result["jobs"]

    def test_dangerous_yaml_content(self) -> None:
        """Test that dangerous YAML content is rejected."""
        dangerous_content = """
name: Malicious
on: push
jobs:
  hack:
    runs-on: ubuntu-latest
    steps:
    - name: Evil step
      run: |
        eval("__import__('os').system('rm -rf /')")
        exec("malicious code here")
"""
        
        with pytest.raises(ValidationError, match="dangerous pattern"):
            InputValidator.validate_yaml_content(dangerous_content)

    def test_realistic_repository_names(self) -> None:
        """Test validation with realistic repository names."""
        real_repos = [
            "facebook/react",
            "microsoft/vscode",
            "python/cpython",
            "nodejs/node",
            "kubernetes/kubernetes",
            "datas-world/github-actions-optimizer",
        ]
        
        for repo in real_repos:
            result = InputValidator.validate_repository_name(repo)
            assert result == repo