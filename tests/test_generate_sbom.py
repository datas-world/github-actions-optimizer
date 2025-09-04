"""Tests for SBOM generation functionality."""

import argparse
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gh_actions_optimizer.generate.sbom.command import cmd_generate_sbom


@pytest.fixture
def mock_args():
    """Create mock arguments for testing."""
    args = argparse.Namespace()
    args.quiet = False
    args.format = "table"
    args.output = None
    return args


@pytest.fixture
def mock_args_quiet():
    """Create mock arguments with quiet mode."""
    args = argparse.Namespace()
    args.quiet = True
    args.format = "table"
    args.output = None
    return args


@pytest.fixture
def mock_args_json():
    """Create mock arguments for JSON output."""
    args = argparse.Namespace()
    args.quiet = False
    args.format = "json"
    args.output = None
    return args


@pytest.fixture
def mock_args_with_output():
    """Create mock arguments with file output."""
    args = argparse.Namespace()
    args.quiet = False
    args.format = "json"
    args.output = "/tmp/test-sbom.json"
    return args


@pytest.fixture
def sample_sbom_data():
    """Sample SBOM data for testing."""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "component": {
                "name": "test-project",
                "version": "1.0.0"
            }
        },
        "components": [
            {
                "name": "rich",
                "version": "13.7.1",
                "type": "library",
                "licenses": [
                    {
                        "license": {
                            "name": "MIT"
                        }
                    }
                ]
            },
            {
                "name": "PyYAML",
                "version": "6.0.1",
                "type": "library",
                "licenses": [
                    {
                        "license": {
                            "name": "MIT"
                        }
                    }
                ]
            }
        ]
    }


class TestSBOMGeneration:
    """Test SBOM generation functionality."""

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_info")
    def test_sbom_generation_table_format(self, mock_log_info, mock_subprocess, mock_args, sample_sbom_data, capsys):
        """Test SBOM generation with table format output."""
        # Mock subprocess response
        mock_result = Mock()
        mock_result.stdout = json.dumps(sample_sbom_data)
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args)

        # Verify subprocess was called correctly with security enhancements
        expected_call = mock_subprocess.call_args
        assert expected_call[0][0] == ["pip-audit", "--format=cyclonedx-json", "--ignore-vuln", "*"]
        assert expected_call[1]["capture_output"] is True
        assert expected_call[1]["text"] is True
        assert expected_call[1]["check"] is True
        assert "env" in expected_call[1]
        assert "timeout" in expected_call[1]

        # Verify log was called
        mock_log_info.assert_called_once_with("Generating Software Bill of Materials (SBOM)...")

        # Check output contains expected content
        captured = capsys.readouterr()
        assert "Software Bill of Materials" in captured.out
        assert "test-project" in captured.out
        assert "Components: 2" in captured.out
        assert "rich" in captured.out and "13.7.1" in captured.out and "MIT" in captured.out
        assert "PyYAML" in captured.out and "6.0.1" in captured.out

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_info")
    def test_sbom_generation_quiet_mode(self, mock_log_info, mock_subprocess, mock_args_quiet, sample_sbom_data):
        """Test SBOM generation in quiet mode."""
        # Mock subprocess response
        mock_result = Mock()
        mock_result.stdout = json.dumps(sample_sbom_data)
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args_quiet)

        # Verify log was NOT called in quiet mode
        mock_log_info.assert_not_called()

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    def test_sbom_generation_json_format(self, mock_subprocess, mock_args_json, sample_sbom_data, capsys):
        """Test SBOM generation with JSON format output."""
        # Mock subprocess response
        mock_result = Mock()
        mock_result.stdout = json.dumps(sample_sbom_data)
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args_json)

        # Check JSON output is properly formatted
        captured = capsys.readouterr()
        output_data = json.loads(captured.out)
        assert output_data["bomFormat"] == "CycloneDX"
        assert len(output_data["components"]) == 2

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_success")
    @patch("pathlib.Path.mkdir")  # Mock directory creation
    def test_sbom_generation_with_file_output(self, mock_mkdir, mock_log_success, mock_subprocess, mock_args_with_output, sample_sbom_data):
        """Test SBOM generation with file output."""
        # Mock subprocess response
        mock_result = Mock()
        mock_result.stdout = json.dumps(sample_sbom_data)
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args_with_output)

        # Verify subprocess was called with output file and security enhancements
        expected_call = mock_subprocess.call_args
        expected_cmd = ["pip-audit", "--format=cyclonedx-json", "--ignore-vuln", "*", "--output", "/tmp/test-sbom.json"]
        assert expected_call[0][0] == expected_cmd
        assert expected_call[1]["capture_output"] is True
        assert expected_call[1]["text"] is True
        assert expected_call[1]["check"] is True
        assert "env" in expected_call[1]
        assert "timeout" in expected_call[1]

        # Verify success message uses validated path (will be the same for /tmp files)
        mock_log_success.assert_called_once()
        success_call_args = mock_log_success.call_args[0][0]
        assert "/tmp/test-sbom.json" in success_call_args

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_error")
    def test_sbom_generation_subprocess_error(self, mock_log_error, mock_subprocess, mock_args):
        """Test SBOM generation with subprocess error."""
        # Mock subprocess to raise CalledProcessError
        error = subprocess.CalledProcessError(1, "pip-audit", stderr="Some error")
        mock_subprocess.side_effect = error

        cmd_generate_sbom(mock_args)

        # Verify error logging
        mock_log_error.assert_any_call("Failed to generate SBOM: Command 'pip-audit' returned non-zero exit status 1.")
        mock_log_error.assert_any_call("Error output: Some error")

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_error")
    def test_sbom_generation_file_not_found(self, mock_log_error, mock_subprocess, mock_args):
        """Test SBOM generation when pip-audit is not found."""
        # Mock subprocess to raise FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError()

        cmd_generate_sbom(mock_args)

        # Verify error logging
        mock_log_error.assert_called_once_with("pip-audit not found. Install with: pip install pip-audit")

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_error")
    def test_sbom_generation_invalid_json(self, mock_log_error, mock_subprocess, mock_args):
        """Test SBOM generation with invalid JSON response."""
        # Mock subprocess to return invalid JSON
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args)

        # Verify error logging
        mock_log_error.assert_called_once()
        assert "Failed to parse SBOM JSON:" in str(mock_log_error.call_args[0][0])

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_error")
    def test_sbom_generation_unexpected_error(self, mock_log_error, mock_subprocess, mock_args):
        """Test SBOM generation with unexpected error."""
        # Mock subprocess to raise unexpected exception
        mock_subprocess.side_effect = RuntimeError("Unexpected error")

        cmd_generate_sbom(mock_args)

        # Verify error logging
        mock_log_error.assert_called_once_with("Unexpected error generating SBOM: Unexpected error")

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    def test_sbom_generation_empty_components(self, mock_subprocess, mock_args, capsys):
        """Test SBOM generation with empty components list."""
        # Mock subprocess response with empty components
        sbom_data = {
            "metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "component": {"name": "empty-project"}
            },
            "components": []
        }
        mock_result = Mock()
        mock_result.stdout = json.dumps(sbom_data)
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args)

        # Check output handles empty components
        captured = capsys.readouterr()
        assert "Components: 0" in captured.out

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    def test_sbom_generation_missing_license_info(self, mock_subprocess, mock_args, capsys):
        """Test SBOM generation with missing license information."""
        # Mock subprocess response with component missing license info
        sbom_data = {
            "metadata": {
                "component": {"name": "test-project"}
            },
            "components": [
                {
                    "name": "no-license-package",
                    "version": "1.0.0"
                    # No licenses field
                }
            ]
        }
        mock_result = Mock()
        mock_result.stdout = json.dumps(sbom_data)
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args)

        # Check output handles missing license info
        captured = capsys.readouterr()
        assert "no-license-package" in captured.out and "1.0.0" in captured.out and "Unknown" in captured.out

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    def test_sbom_generation_missing_metadata(self, mock_subprocess, mock_args, capsys):
        """Test SBOM generation with missing metadata fields."""
        # Mock subprocess response with minimal metadata
        sbom_data = {
            "components": [
                {
                    "name": "test-package",
                    "version": "1.0.0",
                    "licenses": []
                }
            ]
        }
        mock_result = Mock()
        mock_result.stdout = json.dumps(sbom_data)
        mock_subprocess.return_value = mock_result

        cmd_generate_sbom(mock_args)

        # Check output handles missing metadata
        captured = capsys.readouterr()
        assert "Project: Unknown" in captured.out
        assert "Generated: Unknown" in captured.out

    @patch("gh_actions_optimizer.generate.sbom.command.log_error")
    def test_sbom_generation_invalid_output_path(self, mock_log_error):
        """Test SBOM generation with invalid output path (directory traversal)."""
        args = argparse.Namespace()
        args.quiet = False
        args.format = "json"
        args.output = "../../../etc/passwd"  # Directory traversal attempt
        
        cmd_generate_sbom(args)
        
        # Verify error is logged for invalid path
        mock_log_error.assert_called_once()
        error_msg = mock_log_error.call_args[0][0]
        assert "Invalid output path" in error_msg
        assert "Path cannot contain '..' components" in error_msg

    @patch("gh_actions_optimizer.generate.sbom.command.subprocess.run")
    @patch("gh_actions_optimizer.generate.sbom.command.log_error")
    def test_sbom_generation_timeout_error(self, mock_log_error, mock_subprocess, mock_args):
        """Test SBOM generation with subprocess timeout."""
        # Mock subprocess to raise TimeoutExpired
        mock_subprocess.side_effect = subprocess.TimeoutExpired("pip-audit", 60)

        cmd_generate_sbom(mock_args)

        # Verify timeout error logging
        mock_log_error.assert_called_once_with("SBOM generation timed out after 60 seconds")

    @patch("gh_actions_optimizer.generate.sbom.command.log_error")
    def test_sbom_generation_absolute_path_validation(self, mock_log_error):
        """Test SBOM generation with unsafe absolute path."""
        args = argparse.Namespace()
        args.quiet = False
        args.format = "json"
        args.output = "/etc/shadow"  # Unsafe system file
        
        cmd_generate_sbom(args)
        
        # Verify error is logged for unsafe absolute path
        mock_log_error.assert_called_once()
        error_msg = mock_log_error.call_args[0][0]
        assert "Invalid output path" in error_msg
        assert "Absolute paths must be within safe directories" in error_msg


class TestSBOMMainIntegration:
    """Test SBOM integration with command line arguments."""

    def test_argument_parsing_integration(self):
        """Test that SBOM command arguments are properly structured."""
        from gh_actions_optimizer.main import create_parser
        
        parser = create_parser()
        
        # Test SBOM command parsing
        args = parser.parse_args(["generate", "sbom", "--format", "json"])
        assert args.command == "generate"
        assert args.generate_command == "sbom"
        assert args.format == "json"
        
        # Test with output file
        args = parser.parse_args(["generate", "sbom", "--output", "test.json"])
        assert args.output == "test.json"
        
        # Test quiet mode
        args = parser.parse_args(["generate", "sbom", "--quiet"])
        assert args.quiet is True