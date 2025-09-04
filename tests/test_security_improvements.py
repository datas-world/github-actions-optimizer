"""Test security improvements and coverage for security hotspots."""

import os
import subprocess
import tempfile
import unittest.mock
from pathlib import Path

import pytest

from gh_actions_optimizer.shared.cli import Colors, check_dependencies, log_error, log_info, log_success, log_warn
from gh_actions_optimizer.shared.github import download_workflow_content, get_current_repo, run_gh_command
from gh_actions_optimizer.shared.output import format_output, open_in_browser
from gh_actions_optimizer.shared.validation import InputValidator, ValidationError


class TestSecurityImprovements:
    """Test security improvements and edge cases."""

    def test_regex_patterns_no_redos(self):
        """Test that regex patterns don't cause ReDoS attacks."""
        # Test with potentially dangerous input
        dangerous_input = "a" * 10000 + "${"
        
        # This should complete quickly and not hang
        with pytest.raises(ValidationError):
            InputValidator.validate_repository_name(dangerous_input)

    def test_sanitize_for_shell_comprehensive(self):
        """Test comprehensive shell sanitization."""
        dangerous_inputs = [
            "test; rm -rf /",
            "test && rm file",
            "test | cat /etc/passwd",
            "test `whoami`",
            "test $(whoami)",
            "test {echo test}",
            "test <file",
            "test >file", 
            "test *",
            "test ?",
            "test [abc]",
            "test ~user",
            "eval(code)",
            "exec(code)",
            "system(cmd)",
            "popen(cmd)",
            "test\\x41",  # hex escape
            "test\\101",  # octal escape
        ]
        
        for dangerous_input in dangerous_inputs:
            with pytest.raises(ValidationError, match="shell"):
                InputValidator.sanitize_for_shell(dangerous_input)

    def test_environment_variable_validation_edge_cases(self):
        """Test environment variable validation edge cases."""
        # Valid cases
        assert InputValidator.validate_environment_variable("TEST_VAR", "value") == ("TEST_VAR", "value")
        assert InputValidator.validate_environment_variable("_PRIVATE", "secret") == ("_PRIVATE", "secret")
        
        # Invalid name formats
        with pytest.raises(ValidationError):
            InputValidator.validate_environment_variable("123_INVALID", "value")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_environment_variable("test-var", "value")
            
        with pytest.raises(ValidationError):
            InputValidator.validate_environment_variable("test.var", "value")

    def test_github_ref_pattern_security(self):
        """Test GitHub ref pattern with security constraints."""
        # Valid refs
        assert InputValidator.validate_github_ref("main") == "main"
        assert InputValidator.validate_github_ref("feature/test") == "feature/test"
        assert InputValidator.validate_github_ref("v1.0.0") == "v1.0.0"
        
        # Invalid - too long
        with pytest.raises(ValidationError):
            InputValidator.validate_github_ref("a" * 251)
            
        # Invalid - dangerous patterns
        with pytest.raises(ValidationError):
            InputValidator.validate_github_ref("../../../etc/passwd")

    def test_file_extension_validation(self):
        """Test file extension validation."""
        # Valid extensions
        assert InputValidator.validate_file_extension("test.yml", [".yml", ".yaml"]) == "test.yml"
        assert InputValidator.validate_file_extension("TEST.YML", [".yml", ".yaml"]) == "test.yml"
        
        # Invalid extensions
        with pytest.raises(ValidationError):
            InputValidator.validate_file_extension("test.txt", [".yml", ".yaml"])

    def test_dangerous_pattern_detection(self):
        """Test enhanced dangerous pattern detection."""
        dangerous_patterns = [
            "../../../etc/passwd",
            "${DANGEROUS_VAR}",
            "javascript:alert('xss')",
            "<script>alert('xss')</script>",
            "eval(dangerous_code)",
            "exec(malicious)",
            "system('rm -rf /')",
            "import os",
            "__import__('os')",
            "subprocess.call",
            "os.system('cmd')",
        ]
        
        for pattern in dangerous_patterns:
            with pytest.raises(ValidationError):
                InputValidator.validate_repository_name(f"test/{pattern}")


class TestSubprocessSecurity:
    """Test subprocess security improvements."""

    @unittest.mock.patch('shutil.which')
    @unittest.mock.patch('subprocess.run')
    def test_check_dependencies_security(self, mock_run, mock_which):
        """Test secure dependency checking."""
        mock_which.return_value = "/usr/bin/gh"
        mock_run.return_value = subprocess.CompletedProcess(
            args=["/usr/bin/gh", "--version"], 
            returncode=0, 
            stdout="gh version 2.0.0"
        )
        
        # Should not raise any exceptions
        check_dependencies()
        
        # Verify secure environment was used
        mock_run.assert_called()
        call_args = mock_run.call_args
        assert 'env' in call_args.kwargs
        assert 'timeout' in call_args.kwargs

    @unittest.mock.patch('shutil.which')
    def test_check_dependencies_missing(self, mock_which):
        """Test dependency checking with missing tools."""
        mock_which.return_value = None
        
        with pytest.raises(SystemExit):
            check_dependencies()

    @unittest.mock.patch('shutil.which')
    @unittest.mock.patch('subprocess.run')
    def test_run_gh_command_security(self, mock_run, mock_which):
        """Test secure GitHub CLI command execution."""
        mock_which.return_value = "/usr/bin/gh"
        mock_run.return_value = subprocess.CompletedProcess(
            args=["/usr/bin/gh", "repo", "view"], 
            returncode=0, 
            stdout='{"nameWithOwner": "test/repo"}'
        )
        
        result = run_gh_command(["repo", "view"])
        
        # Verify secure execution
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.args[0][0] == "/usr/bin/gh"
        assert 'timeout' in call_args.kwargs
        assert 'env' in call_args.kwargs

    def test_run_gh_command_invalid_args(self):
        """Test GitHub CLI command with invalid arguments."""
        with pytest.raises(SystemExit):
            run_gh_command([123])  # Invalid argument type


class TestURLSecurity:
    """Test URL security improvements."""

    @unittest.mock.patch('urllib.request.urlopen')
    def test_download_workflow_content_security(self, mock_urlopen):
        """Test secure workflow content download."""
        mock_response = unittest.mock.MagicMock()
        mock_response.read.return_value = b"name: test\nruns-on: ubuntu-latest"
        mock_response.headers.get.return_value = "text/yaml"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        content = download_workflow_content("https://github.com/user/repo/raw/main/.github/workflows/test.yml")
        
        assert "name: test" in content

    def test_download_workflow_content_invalid_domain(self):
        """Test workflow download with invalid domain."""
        content = download_workflow_content("https://evil.com/malicious.yml")
        assert content == ""

    @unittest.mock.patch('webbrowser.open')
    def test_open_in_browser_security(self, mock_open):
        """Test secure browser opening."""
        open_in_browser("https://github.com/pricing")
        mock_open.assert_called_once_with("https://github.com/pricing")

    def test_open_in_browser_invalid_url(self):
        """Test browser opening with invalid URL."""
        with pytest.raises(SystemExit):
            open_in_browser("javascript:alert('xss')")


class TestColorHandling:
    """Test color handling security."""

    def test_color_environment_validation(self):
        """Test color environment variable validation."""
        colors = Colors()
        
        # Test with clean environment
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            # Force color should be false with no environment
            assert not colors._should_force_color()
            # Disable color result depends on TTY status, which is fine
            result = colors._should_disable_color()
            assert isinstance(result, bool)

    @unittest.mock.patch.dict(os.environ, {"FORCE_COLOR": "$(malicious)"})
    def test_color_environment_sanitization(self):
        """Test color environment variable sanitization."""
        colors = Colors()
        # Should not crash and should handle malicious input safely
        assert not colors._should_force_color()


class TestFileOperationSecurity:
    """Test file operation security."""

    def test_format_output_file_security(self):
        """Test secure file output operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test.json")
            
            format_output({"test": "data"}, "json", output_file)
            
            # Verify file was created with secure permissions
            assert os.path.exists(output_file)
            stat_info = os.stat(output_file)
            # Check that file permissions are restrictive (owner read/write only)
            assert oct(stat_info.st_mode)[-3:] == "640"

    def test_format_output_directory_traversal_protection(self):
        """Test protection against directory traversal in output files."""
        with pytest.raises(SystemExit):
            format_output({"test": "data"}, "json", "/etc/passwd")

    def test_format_output_secure_directory_creation(self):
        """Test secure directory creation for output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "subdir", "test.json")
            
            format_output({"test": "data"}, "json", nested_path)
            
            # Verify directory was created with secure permissions
            subdir = os.path.dirname(nested_path)
            assert os.path.exists(subdir)
            stat_info = os.stat(subdir)
            # Check directory permissions
            assert oct(stat_info.st_mode)[-3:] == "750"


class TestRepositoryDetectionSecurity:
    """Test repository detection security."""

    @unittest.mock.patch.dict(os.environ, {"GITHUB_REPOSITORY": "valid/repo"})
    def test_github_repository_env_validation(self):
        """Test GitHub repository environment variable validation."""
        repo = get_current_repo()
        assert repo == "valid/repo"

    @unittest.mock.patch.dict(os.environ, {"GITHUB_REPOSITORY": "../../../malicious"})
    def test_github_repository_env_invalid(self):
        """Test invalid GitHub repository environment variable."""
        # Should fall through to other detection methods due to validation failure
        with unittest.mock.patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'gh')
            repo = get_current_repo()
            assert repo is None

    @unittest.mock.patch('subprocess.run')
    def test_git_remote_url_validation(self, mock_run):
        """Test git remote URL validation."""
        # Test with valid GitHub URL
        mock_run.return_value = subprocess.CompletedProcess(
            args=['git', 'remote', 'get-url', 'origin'],
            returncode=0,
            stdout='https://github.com/user/repo.git\n'
        )
        
        # Mock the other subprocess calls to fail so we get to git remote
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            with unittest.mock.patch('subprocess.run') as mock_run_all:
                def side_effect(*args, **kwargs):
                    if 'gh' in args[0]:
                        raise subprocess.CalledProcessError(1, 'gh')
                    else:  # git command
                        return subprocess.CompletedProcess(
                            args=['git', 'remote', 'get-url', 'origin'],
                            returncode=0,
                            stdout='https://github.com/user/repo.git\n'
                        )
                mock_run_all.side_effect = side_effect
                
                repo = get_current_repo()
                assert repo == "user/repo"

    @unittest.mock.patch('subprocess.run')
    def test_git_remote_url_too_long(self, mock_run):
        """Test git remote URL that's too long."""
        long_url = "https://github.com/" + "a" * 2048 + "/repo.git"
        mock_run.return_value = subprocess.CompletedProcess(
            args=['git', 'remote', 'get-url', 'origin'],
            returncode=0,
            stdout=long_url + '\n'
        )
        
        repo = get_current_repo()
        assert repo is None


class TestLoggingFunctions:
    """Test logging function coverage."""

    @unittest.mock.patch('gh_actions_optimizer.shared.cli.colors')
    def test_logging_functions(self, mock_colors):
        """Test all logging functions for coverage."""
        mock_console = unittest.mock.MagicMock()
        mock_colors.get_console.return_value = mock_console
        
        log_info("test info")
        log_warn("test warning")
        log_error("test error")
        log_success("test success")
        
        assert mock_console.print.call_count == 4


class TestYAMLContentValidation:
    """Test YAML content validation edge cases."""

    def test_yaml_validation_empty_dict(self):
        """Test YAML validation with empty dictionary."""
        with pytest.raises(ValidationError, match="empty or invalid"):
            InputValidator.validate_yaml_content("null")

    def test_yaml_validation_non_dict(self):
        """Test YAML validation with non-dictionary content."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            InputValidator.validate_yaml_content("- item1\n- item2")

    def test_yaml_validation_dangerous_content(self):
        """Test YAML validation with dangerous content."""
        dangerous_yaml = """
        name: test
        script: |
          eval(dangerous_code)
        """
        with pytest.raises(ValidationError, match="dangerous pattern"):
            InputValidator.validate_yaml_content(dangerous_yaml)