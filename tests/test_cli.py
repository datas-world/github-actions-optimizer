"""Tests for CLI utilities."""

import argparse
import os
import sys
from io import StringIO
from unittest.mock import Mock, patch

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

    def test_colors_init_default(self) -> None:
        """Test Colors initialization with default settings."""
        color_obj = Colors()
        assert color_obj._console_stdout is not None
        assert color_obj._console_stderr is not None

    def test_should_force_color_true(self) -> None:
        """Test force color detection returns True."""
        color_obj = Colors()
        
        # Test various true values
        test_values = ["1", "true", "True", "TRUE"]
        for value in test_values:
            with patch.dict(os.environ, {"FORCE_COLOR": value}):
                assert color_obj._should_force_color() is True

    def test_should_force_color_false(self) -> None:
        """Test force color detection returns False."""
        color_obj = Colors()
        
        with patch.dict(os.environ, {}, clear=True):
            assert color_obj._should_force_color() is False
            
        with patch.dict(os.environ, {"FORCE_COLOR": "0"}):
            assert color_obj._should_force_color() is False

    def test_should_disable_color_force_color_zero(self) -> None:
        """Test color disabled when FORCE_COLOR=0."""
        color_obj = Colors()
        
        with patch.dict(os.environ, {"FORCE_COLOR": "0"}):
            assert color_obj._should_disable_color() is True

    def test_should_disable_color_no_color_set(self) -> None:
        """Test color disabled when NO_COLOR is set."""
        color_obj = Colors()
        
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            assert color_obj._should_disable_color() is True

    def test_should_disable_color_no_color_with_force(self) -> None:
        """Test NO_COLOR overridden by FORCE_COLOR=1."""
        color_obj = Colors()
        
        with patch.dict(os.environ, {"NO_COLOR": "1", "FORCE_COLOR": "1"}):
            assert color_obj._should_disable_color() is False

    def test_should_disable_color_not_tty(self) -> None:
        """Test color disabled when not a TTY."""
        color_obj = Colors()
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stderr.isatty", return_value=False):
                assert color_obj._should_disable_color() is True

    def test_should_disable_color_not_tty_with_force(self) -> None:
        """Test TTY check overridden by explicit force."""
        color_obj = Colors()
        
        test_values = ["1", "true", "True", "TRUE"]
        for value in test_values:
            with patch.dict(os.environ, {"FORCE_COLOR": value}):
                with patch("sys.stderr.isatty", return_value=False):
                    assert color_obj._should_disable_color() is False

    def test_get_console_stdout(self) -> None:
        """Test getting stdout console."""
        color_obj = Colors()
        console = color_obj.get_console(sys.stdout)
        assert console is color_obj._console_stdout

    def test_get_console_stderr(self) -> None:
        """Test getting stderr console (default)."""
        color_obj = Colors()
        console = color_obj.get_console(sys.stderr)
        assert console is color_obj._console_stderr
        
        # Test default parameter
        console_default = color_obj.get_console()
        assert console_default is color_obj._console_stderr

    def test_color_methods_with_color(self) -> None:
        """Test color methods when color is enabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, '_should_disable_color', return_value=False):
            assert color_obj.red("test") == "[red]test[/red]"
            assert color_obj.green("test") == "[green]test[/green]"
            assert color_obj.yellow("test") == "[yellow]test[/yellow]"
            assert color_obj.blue("test") == "[blue]test[/blue]"
            assert color_obj.bold("test") == "[bold]test[/bold]"

    def test_color_methods_without_color(self) -> None:
        """Test color methods when color is disabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, '_should_disable_color', return_value=True):
            assert color_obj.red("test") == "test"
            assert color_obj.green("test") == "test"
            assert color_obj.yellow("test") == "test"
            assert color_obj.blue("test") == "test"
            assert color_obj.bold("test") == "test"

    def test_legacy_ansi_properties_with_color(self) -> None:
        """Test legacy ANSI properties when color is enabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, '_should_disable_color', return_value=False):
            assert color_obj.RED != ""
            assert color_obj.GREEN != ""
            assert color_obj.YELLOW != ""
            assert color_obj.BLUE != ""
            assert color_obj.BOLD != ""
            assert color_obj.NC != ""

    def test_legacy_ansi_properties_without_color(self) -> None:
        """Test legacy ANSI properties when color is disabled."""
        color_obj = Colors()
        
        with patch.object(color_obj, '_should_disable_color', return_value=True):
            assert color_obj.RED == ""
            assert color_obj.GREEN == ""
            assert color_obj.YELLOW == ""
            assert color_obj.BLUE == ""
            assert color_obj.BOLD == ""
            assert color_obj.NC == ""


class TestLoggingFunctions:
    """Test logging functions."""

    def test_log_info(self) -> None:
        """Test log_info function."""
        with patch.object(colors, 'get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            log_info("test message")
            
            mock_get_console.assert_called_once_with(sys.stderr)
            mock_console.print.assert_called_once_with("[blue][INFO][/blue] test message", highlight=False)

    def test_log_warn(self) -> None:
        """Test log_warn function."""
        with patch.object(colors, 'get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            log_warn("test warning")
            
            mock_get_console.assert_called_once_with(sys.stderr)
            mock_console.print.assert_called_once_with("[yellow][WARN][/yellow] test warning", highlight=False)

    def test_log_error(self) -> None:
        """Test log_error function."""
        with patch.object(colors, 'get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            log_error("test error")
            
            mock_get_console.assert_called_once_with(sys.stderr)
            mock_console.print.assert_called_once_with("[red][ERROR][/red] test error", highlight=False)

    def test_log_success(self) -> None:
        """Test log_success function."""
        with patch.object(colors, 'get_console') as mock_get_console:
            mock_console = Mock()
            mock_get_console.return_value = mock_console
            
            log_success("test success")
            
            mock_get_console.assert_called_once_with(sys.stderr)
            mock_console.print.assert_called_once_with("[green][SUCCESS][/green] test success", highlight=False)


class TestArgumentParsers:
    """Test argument parser functions."""

    def test_add_common_args_not_required(self) -> None:
        """Test adding common arguments without required repo."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, repo_required=False)
        
        # Test that all expected arguments are added
        args = parser.parse_args([])
        assert hasattr(args, 'repo')
        assert hasattr(args, 'format')
        assert hasattr(args, 'output')
        assert hasattr(args, 'verbose')
        assert hasattr(args, 'quiet')
        assert hasattr(args, 'web')
        
        # Test defaults
        assert args.format == 'table'
        assert args.verbose is False
        assert args.quiet is False
        assert args.web is False

    def test_add_common_args_required(self) -> None:
        """Test adding common arguments with required repo."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, repo_required=True)
        
        # Should fail without repo
        with pytest.raises(SystemExit):
            parser.parse_args([])
            
        # Should work with repo
        args = parser.parse_args(['-R', 'owner/repo'])
        assert args.repo == 'owner/repo'

    def test_add_common_args_with_values(self) -> None:
        """Test common arguments with specific values."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        
        args = parser.parse_args([
            '-R', 'owner/repo',
            '-f', 'json', 
            '-o', 'output.txt',
            '-v',
            '-q',
            '-w'
        ])
        
        assert args.repo == 'owner/repo'
        assert args.format == 'json'
        assert args.output == 'output.txt'
        assert args.verbose is True
        assert args.quiet is True
        assert args.web is True

    def test_add_output_args(self) -> None:
        """Test adding output-only arguments."""
        parser = argparse.ArgumentParser()
        add_output_args(parser)
        
        args = parser.parse_args([])
        assert hasattr(args, 'format')
        assert hasattr(args, 'output')
        assert hasattr(args, 'quiet')
        assert args.format == 'table'
        assert args.quiet is False

    def test_add_output_args_with_values(self) -> None:
        """Test output arguments with specific values."""
        parser = argparse.ArgumentParser()
        add_output_args(parser)
        
        args = parser.parse_args(['-f', 'yaml', '-o', 'out.yaml', '-q'])
        assert args.format == 'yaml'
        assert args.output == 'out.yaml'
        assert args.quiet is True


class TestCheckDependencies:
    """Test dependency checking function."""

    def test_check_dependencies_all_available(self) -> None:
        """Test dependency check when all dependencies are available."""
        with patch("gh_actions_optimizer.shared.subprocess.check_command_availability") as mock_check:
            mock_check.return_value = True
            
            # Should not raise or exit
            check_dependencies()
            
            # Should check for both gh and jq
            assert mock_check.call_count == 2
            mock_check.assert_any_call("gh")
            mock_check.assert_any_call("jq")

    def test_check_dependencies_missing_gh(self) -> None:
        """Test dependency check when gh is missing."""
        def side_effect(cmd: str) -> bool:
            return cmd != "gh"
            
        with patch("gh_actions_optimizer.shared.subprocess.check_command_availability", side_effect=side_effect):
            with pytest.raises(SystemExit):
                check_dependencies()

    def test_check_dependencies_missing_jq(self) -> None:
        """Test dependency check when jq is missing."""
        def side_effect(cmd: str) -> bool:
            return cmd != "jq"
            
        with patch("gh_actions_optimizer.shared.subprocess.check_command_availability", side_effect=side_effect):
            with pytest.raises(SystemExit):
                check_dependencies()

    def test_check_dependencies_missing_both(self) -> None:
        """Test dependency check when both dependencies are missing."""
        with patch("gh_actions_optimizer.shared.subprocess.check_command_availability", return_value=False):
            with pytest.raises(SystemExit):
                check_dependencies()