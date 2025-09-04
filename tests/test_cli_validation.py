"""Tests for CLI validation integration."""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from gh_actions_optimizer.shared.cli import (
    Colors,
    validate_parsed_args,
    log_error,
    log_info,
    log_warn,
    log_success,
)


class TestColors:
    """Test cases for Colors class."""

    def test_colors_initialization(self) -> None:
        """Test Colors class initialization."""
        colors = Colors()
        assert colors is not None

    def test_should_force_color(self) -> None:
        """Test force color detection."""
        colors = Colors()
        
        # Test with FORCE_COLOR=1
        with patch.dict(os.environ, {"FORCE_COLOR": "1"}):
            colors_forced = Colors()
            assert colors_forced._should_force_color() is True
        
        # Test with FORCE_COLOR=true
        with patch.dict(os.environ, {"FORCE_COLOR": "true"}):
            colors_forced = Colors()
            assert colors_forced._should_force_color() is True
        
        # Test with invalid FORCE_COLOR
        with patch.dict(os.environ, {"FORCE_COLOR": "invalid$chars"}):
            colors_safe = Colors()
            assert colors_safe._should_force_color() is False

    def test_should_disable_color(self) -> None:
        """Test color disable detection."""
        colors = Colors()
        
        # Test with NO_COLOR set
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            colors_disabled = Colors()
            assert colors_disabled._should_disable_color() is True
        
        # Test with FORCE_COLOR=0
        with patch.dict(os.environ, {"FORCE_COLOR": "0"}):
            colors_disabled = Colors()
            assert colors_disabled._should_disable_color() is True
        
        # Test with invalid environment variables
        with patch.dict(os.environ, {"NO_COLOR": "invalid$chars", "FORCE_COLOR": "bad$value"}):
            colors_safe = Colors()
            # Should handle invalid characters safely
            assert isinstance(colors_safe._should_disable_color(), bool)

    def test_color_methods(self) -> None:
        """Test color formatting methods."""
        colors = Colors()
        
        # Test basic color methods
        assert isinstance(colors.red("test"), str)
        assert isinstance(colors.green("test"), str)
        assert isinstance(colors.yellow("test"), str)
        assert isinstance(colors.blue("test"), str)
        assert isinstance(colors.bold("test"), str)
        
        # Test legacy properties
        assert isinstance(colors.RED, str)
        assert isinstance(colors.GREEN, str)
        assert isinstance(colors.YELLOW, str)
        assert isinstance(colors.BLUE, str)
        assert isinstance(colors.BOLD, str)
        assert isinstance(colors.NC, str)

    def test_get_console(self) -> None:
        """Test console retrieval."""
        colors = Colors()
        
        stdout_console = colors.get_console(sys.stdout)
        stderr_console = colors.get_console(sys.stderr)
        
        assert stdout_console is not None
        assert stderr_console is not None
        # Default should be stderr
        default_console = colors.get_console()
        assert default_console is stderr_console


class TestLoggingFunctions:
    """Test cases for logging functions."""

    def test_log_info(self) -> None:
        """Test info logging."""
        # Just test that the function runs without error
        log_info("Test info message")

    def test_log_warn(self) -> None:
        """Test warning logging."""
        # Just test that the function runs without error
        log_warn("Test warning message")

    def test_log_error(self) -> None:
        """Test error logging."""
        # Just test that the function runs without error
        log_error("Test error message")

    def test_log_success(self) -> None:
        """Test success logging."""
        # Just test that the function runs without error
        log_success("Test success message")


class TestValidateParsedArgs:
    """Test cases for validate_parsed_args function."""

    def test_validate_repository_valid(self) -> None:
        """Test valid repository validation."""
        args = argparse.Namespace()
        args.repo = "owner/repo"
        
        # Should not raise any exception
        validate_parsed_args(args)

    def test_validate_repository_invalid(self) -> None:
        """Test invalid repository validation."""
        args = argparse.Namespace()
        args.repo = "../malicious"
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_output_file_valid(self) -> None:
        """Test valid output file validation."""
        args = argparse.Namespace()
        args.output = "output.json"
        
        # Should not raise any exception
        validate_parsed_args(args)

    def test_validate_output_file_invalid(self) -> None:
        """Test invalid output file validation."""
        args = argparse.Namespace()
        args.output = "../../../etc/passwd"
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_workflow_file_valid(self) -> None:
        """Test valid workflow file validation."""
        args = argparse.Namespace()
        args.workflow = "workflow.yml"
        
        # Should not raise any exception
        validate_parsed_args(args)

    def test_validate_workflow_file_invalid_path(self) -> None:
        """Test invalid workflow file path."""
        args = argparse.Namespace()
        args.workflow = "../malicious.yml"
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_workflow_file_invalid_extension(self) -> None:
        """Test invalid workflow file extension."""
        args = argparse.Namespace()
        args.workflow = "workflow.txt"
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_format_valid(self) -> None:
        """Test valid format validation."""
        args = argparse.Namespace()
        args.format = "json"
        
        # Should not raise any exception
        validate_parsed_args(args)

    def test_validate_format_invalid(self) -> None:
        """Test invalid format validation."""
        args = argparse.Namespace()
        args.format = "invalid"
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_duration_valid(self) -> None:
        """Test valid duration validation."""
        args = argparse.Namespace()
        args.duration = 30
        
        # Should not raise any exception
        validate_parsed_args(args)

    def test_validate_duration_invalid_negative(self) -> None:
        """Test invalid negative duration."""
        args = argparse.Namespace()
        args.duration = -1
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_duration_invalid_too_large(self) -> None:
        """Test invalid too large duration."""
        args = argparse.Namespace()
        args.duration = 400
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_duration_invalid_type(self) -> None:
        """Test invalid duration type."""
        args = argparse.Namespace()
        args.duration = "invalid"
        
        with pytest.raises(SystemExit):
            validate_parsed_args(args)

    def test_validate_empty_args(self) -> None:
        """Test validation with no relevant arguments."""
        args = argparse.Namespace()
        
        # Should not raise any exception
        validate_parsed_args(args)

    def test_validate_none_values(self) -> None:
        """Test validation with None values."""
        args = argparse.Namespace()
        args.repo = None
        args.output = None
        args.workflow = None
        args.format = None
        args.duration = None
        
        # Should not raise any exception
        validate_parsed_args(args)