"""Tests for CLI utilities."""

import os
import sys
import subprocess
import argparse
from unittest.mock import Mock, patch, MagicMock
import pytest

from gh_actions_optimizer.shared.cli import (
    Colors,
    colors,
    log_info,
    log_warn,
    log_error,
    log_success,
    add_common_args,
    add_output_args,
    check_dependencies,
)


class TestColors:
    """Test Colors class functionality."""

    def test_colors_init(self):
        """Test Colors class initialization."""
        color_obj = Colors()
        assert color_obj._console_stdout is not None
        assert color_obj._console_stderr is not None

    def test_should_force_color(self):
        """Test color forcing logic."""
        color_obj = Colors()
        
        # Test FORCE_COLOR=1
        with patch.dict(os.environ, {"FORCE_COLOR": "1"}):
            assert color_obj._should_force_color() is True
        
        # Test FORCE_COLOR=true
        with patch.dict(os.environ, {"FORCE_COLOR": "true"}):
            assert color_obj._should_force_color() is True
        
        # Test FORCE_COLOR=false
        with patch.dict(os.environ, {"FORCE_COLOR": "false"}):
            assert color_obj._should_force_color() is False
        
        # Test no FORCE_COLOR
        with patch.dict(os.environ, {}, clear=True):
            assert color_obj._should_force_color() is False

    def test_should_disable_color(self):
        """Test color disabling logic."""
        color_obj = Colors()
        
        # Test FORCE_COLOR=0 explicitly disables
        with patch.dict(os.environ, {"FORCE_COLOR": "0"}):
            assert color_obj._should_disable_color() is True
        
        # Test NO_COLOR without FORCE_COLOR=1
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            assert color_obj._should_disable_color() is True
        
        # Test NO_COLOR with FORCE_COLOR=1 (should not disable)
        with patch.dict(os.environ, {"NO_COLOR": "1", "FORCE_COLOR": "1"}):
            assert color_obj._should_disable_color() is False
        
        # Test non-TTY without explicit force
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys.stderr, "isatty", return_value=False):
                assert color_obj._should_disable_color() is True

    def test_get_console(self):
        """Test console retrieval."""
        color_obj = Colors()
        
        # Test stdout console
        stdout_console = color_obj.get_console(sys.stdout)
        assert stdout_console == color_obj._console_stdout
        
        # Test stderr console (default)
        stderr_console = color_obj.get_console(sys.stderr)
        assert stderr_console == color_obj._console_stderr
        
        # Test default (should be stderr)
        default_console = color_obj.get_console()
        assert default_console == color_obj._console_stderr

    def test_color_methods_enabled(self):
        """Test color methods when colors are enabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, "_should_disable_color", return_value=False):
            assert color_obj.red("test") == "[red]test[/red]"
            assert color_obj.green("test") == "[green]test[/green]"
            assert color_obj.yellow("test") == "[yellow]test[/yellow]"
            assert color_obj.blue("test") == "[blue]test[/blue]"
            assert color_obj.bold("test") == "[bold]test[/bold]"

    def test_color_methods_disabled(self):
        """Test color methods when colors are disabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, "_should_disable_color", return_value=True):
            assert color_obj.red("test") == "test"
            assert color_obj.green("test") == "test"
            assert color_obj.yellow("test") == "test"
            assert color_obj.blue("test") == "test"
            assert color_obj.bold("test") == "test"

    def test_legacy_properties_enabled(self):
        """Test legacy ANSI properties when colors are enabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, "_should_disable_color", return_value=False):
            assert color_obj.RED == "\033[0;31m"
            assert color_obj.GREEN == "\033[0;32m"
            assert color_obj.YELLOW == "\033[1;33m"
            assert color_obj.BLUE == "\033[0;34m"
            assert color_obj.BOLD == "\033[1m"
            assert color_obj.NC == "\033[0m"

    def test_legacy_properties_disabled(self):
        """Test legacy ANSI properties when colors are disabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, "_should_disable_color", return_value=True):
            assert color_obj.RED == ""
            assert color_obj.GREEN == ""
            assert color_obj.YELLOW == ""
            assert color_obj.BLUE == ""
            assert color_obj.BOLD == ""
            assert color_obj.NC == ""


class TestLoggingFunctions:
    """Test logging functions."""

    @patch("gh_actions_optimizer.shared.cli.colors.get_console")
    @patch("gh_actions_optimizer.shared.security.sanitize_for_logging")
    def test_log_info(self, mock_sanitize, mock_get_console):
        """Test log_info function."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        mock_sanitize.return_value = "sanitized message"
        
        log_info("test message")
        
        mock_sanitize.assert_called_once_with("test message")
        mock_get_console.assert_called_once_with(sys.stderr)
        mock_console.print.assert_called_once_with("[blue][INFO][/blue] sanitized message", highlight=False)

    @patch("gh_actions_optimizer.shared.cli.colors.get_console")
    @patch("gh_actions_optimizer.shared.security.sanitize_for_logging")
    def test_log_warn(self, mock_sanitize, mock_get_console):
        """Test log_warn function."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        mock_sanitize.return_value = "sanitized warning"
        
        log_warn("test warning")
        
        mock_sanitize.assert_called_once_with("test warning")
        mock_get_console.assert_called_once_with(sys.stderr)
        mock_console.print.assert_called_once_with("[yellow][WARN][/yellow] sanitized warning", highlight=False)

    @patch("gh_actions_optimizer.shared.cli.colors.get_console")
    @patch("gh_actions_optimizer.shared.security.sanitize_error_message")
    def test_log_error(self, mock_sanitize, mock_get_console):
        """Test log_error function."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        mock_sanitize.return_value = "sanitized error"
        
        log_error("test error")
        
        mock_sanitize.assert_called_once_with("test error")
        mock_get_console.assert_called_once_with(sys.stderr)
        mock_console.print.assert_called_once_with("[red][ERROR][/red] sanitized error", highlight=False)

    @patch("gh_actions_optimizer.shared.cli.colors.get_console")
    @patch("gh_actions_optimizer.shared.security.sanitize_for_logging")
    def test_log_success(self, mock_sanitize, mock_get_console):
        """Test log_success function."""
        mock_console = Mock()
        mock_get_console.return_value = mock_console
        mock_sanitize.return_value = "sanitized success"
        
        log_success("test success")
        
        mock_sanitize.assert_called_once_with("test success")
        mock_get_console.assert_called_once_with(sys.stderr)
        mock_console.print.assert_called_once_with("[green][SUCCESS][/green] sanitized success", highlight=False)


class TestArgumentHelpers:
    """Test argument helper functions."""

    def test_add_common_args_required(self):
        """Test add_common_args with required repo."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, repo_required=True)
        
        # Check that required arguments were added
        args = parser.parse_args(["-R", "owner/repo"])
        assert args.repo == "owner/repo"
        assert args.format == "table"  # default
        assert args.verbose is False  # default
        assert args.quiet is False  # default
        assert args.web is False  # default

    def test_add_common_args_not_required(self):
        """Test add_common_args without required repo."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, repo_required=False)
        
        # Should be able to parse without repo
        args = parser.parse_args([])
        assert args.repo is None
        assert args.format == "table"

    def test_add_common_args_all_options(self):
        """Test add_common_args with all options."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, repo_required=False)
        
        args = parser.parse_args([
            "--repo", "owner/repo",
            "--format", "json",
            "--output", "output.json",
            "--verbose",
            "--quiet",
            "--web"
        ])
        
        assert args.repo == "owner/repo"
        assert args.format == "json"
        assert args.output == "output.json"
        assert args.verbose is True
        assert args.quiet is True
        assert args.web is True

    def test_add_output_args(self):
        """Test add_output_args function."""
        parser = argparse.ArgumentParser()
        add_output_args(parser)
        
        args = parser.parse_args([
            "--format", "yaml",
            "--output", "output.yaml",
            "--quiet"
        ])
        
        assert args.format == "yaml"
        assert args.output == "output.yaml"
        assert args.quiet is True


class TestCheckDependencies:
    """Test check_dependencies function."""

    @patch("subprocess.run")
    def test_check_dependencies_all_available(self, mock_run):
        """Test check_dependencies when all dependencies are available."""
        mock_run.return_value = Mock()  # Successful return
        
        # Should not raise SystemExit
        check_dependencies()
        
        # Should have checked both gh and jq
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["gh", "--version"], capture_output=True, check=True)
        mock_run.assert_any_call(["jq", "--version"], capture_output=True, check=True)

    @patch("subprocess.run")
    @patch("sys.exit")
    def test_check_dependencies_gh_missing(self, mock_exit, mock_run):
        """Test check_dependencies when gh is missing."""
        def side_effect(args, **kwargs):
            if args[0] == "gh":
                raise FileNotFoundError()
            return Mock()
        
        mock_run.side_effect = side_effect
        
        check_dependencies()
        
        mock_exit.assert_called_once_with(1)

    @patch("subprocess.run")
    @patch("sys.exit")
    def test_check_dependencies_jq_missing(self, mock_exit, mock_run):
        """Test check_dependencies when jq is missing."""
        def side_effect(args, **kwargs):
            if args[0] == "jq":
                raise subprocess.CalledProcessError(1, "jq")
            return Mock()
        
        mock_run.side_effect = side_effect
        
        check_dependencies()
        
        mock_exit.assert_called_once_with(1)

    @patch("subprocess.run")
    @patch("sys.exit")
    def test_check_dependencies_both_missing(self, mock_exit, mock_run):
        """Test check_dependencies when both dependencies are missing."""
        mock_run.side_effect = FileNotFoundError()
        
        check_dependencies()
        
        mock_exit.assert_called_once_with(1)


class TestGlobalColorsInstance:
    """Test the global colors instance."""

    def test_global_colors_instance(self):
        """Test that the global colors instance is properly initialized."""
        assert colors is not None
        assert isinstance(colors, Colors)
        assert hasattr(colors, 'get_console')
        assert hasattr(colors, 'red')
        assert hasattr(colors, 'green')