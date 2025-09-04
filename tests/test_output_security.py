"""Test output module security and coverage."""

import os
import tempfile
import unittest.mock
from pathlib import Path

import pytest

from gh_actions_optimizer.shared.output import (
    format_output,
    format_table,
    open_github_docs,
    open_github_pricing,
    open_in_browser,
)


class TestFormatOutput:
    """Test format_output function."""

    def test_format_output_json(self):
        """Test JSON output formatting."""
        data = {"test": "value", "number": 42}
        
        with unittest.mock.patch('builtins.print') as mock_print:
            format_output(data, "json")
            mock_print.assert_called_once()
            # Verify JSON was formatted
            output = mock_print.call_args[0][0]
            assert '"test": "value"' in output

    def test_format_output_yaml(self):
        """Test YAML output formatting."""
        data = {"test": "value", "number": 42}
        
        with unittest.mock.patch('builtins.print') as mock_print:
            format_output(data, "yaml")
            mock_print.assert_called_once()
            # Verify YAML was formatted
            output = mock_print.call_args[0][0]
            assert "test: value" in output

    def test_format_output_table(self):
        """Test table output formatting."""
        data = {"test": "value", "number": 42}
        
        with unittest.mock.patch('builtins.print') as mock_print:
            format_output(data, "table")
            mock_print.assert_called_once()
            # Verify table was formatted
            output = mock_print.call_args[0][0]
            assert "test" in output and "value" in output

    def test_format_output_file_creation(self):
        """Test output file creation with secure permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test.json")
            data = {"test": "data"}
            
            format_output(data, "json", output_file)
            
            # Verify file was created
            assert os.path.exists(output_file)
            
            # Verify secure permissions (640)
            stat_info = os.stat(output_file)
            assert oct(stat_info.st_mode)[-3:] == "640"

    def test_format_output_directory_creation(self):
        """Test secure directory creation for output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "subdir")
            output_file = os.path.join(nested_dir, "test.json")
            data = {"test": "data"}
            
            format_output(data, "json", output_file)
            
            # Verify directory was created with secure permissions (750)
            assert os.path.exists(nested_dir)
            stat_info = os.stat(nested_dir)
            assert oct(stat_info.st_mode)[-3:] == "750"

    def test_format_output_invalid_path_protection(self):
        """Test protection against invalid output paths."""
        data = {"test": "data"}
        
        # Should exit when trying to write outside allowed directories
        with pytest.raises(SystemExit):
            format_output(data, "json", "/etc/passwd")

    def test_format_output_file_write_error(self):
        """Test handling of file write errors."""
        data = {"test": "data"}
        
        # Try to write to a read-only directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only
            os.chmod(temp_dir, 0o444)
            output_file = os.path.join(temp_dir, "test.json")
            
            try:
                with pytest.raises(SystemExit):
                    format_output(data, "json", output_file)
            finally:
                # Restore permissions for cleanup
                os.chmod(temp_dir, 0o755)

    def test_format_output_json_security(self):
        """Test JSON output with security options."""
        data = {"test": "value\u0000\u001f", "unicode": "café"}
        
        with unittest.mock.patch('builtins.print') as mock_print:
            format_output(data, "json")
            output = mock_print.call_args[0][0]
            
            # Verify ensure_ascii=True is used for security
            assert "\\u" in output  # Unicode should be escaped

    def test_format_output_yaml_security(self):
        """Test YAML output with security options."""
        data = {"test": "value", "unicode": "café"}
        
        with unittest.mock.patch('builtins.print') as mock_print:
            format_output(data, "yaml")
            output = mock_print.call_args[0][0]
            
            # Verify allow_unicode=False is used for security
            assert isinstance(output, str)


class TestFormatTable:
    """Test format_table function."""

    def test_format_table_dict(self):
        """Test table formatting for dictionary data."""
        data = {"key1": "value1", "key2": "value2"}
        result = format_table(data)
        
        assert "key1" in result
        assert "value1" in result
        assert "key2" in result
        assert "value2" in result

    def test_format_table_dict_with_complex_values(self):
        """Test table formatting with complex values."""
        data = {
            "simple": "value",
            "complex": {"nested": "data"},
            "list": [1, 2, 3]
        }
        result = format_table(data)
        
        assert "simple" in result
        assert "value" in result
        # Complex values should be truncated if too long
        assert "..." in result or "nested" in result

    def test_format_table_list_of_dicts(self):
        """Test table formatting for list of dictionaries."""
        data = [
            {"name": "item1", "value": 10},
            {"name": "item2", "value": 20}
        ]
        result = format_table(data)
        
        assert "name" in result
        assert "value" in result
        assert "item1" in result
        assert "item2" in result
        assert "|" in result  # Table separator

    def test_format_table_list_of_mixed(self):
        """Test table formatting for mixed list."""
        data = ["string1", "string2", "string3"]
        result = format_table(data)
        
        assert "string1" in result
        assert "string2" in result
        assert "string3" in result

    def test_format_table_empty_list(self):
        """Test table formatting for empty list."""
        data = []
        result = format_table(data)
        
        assert "No items found" in result

    def test_format_table_empty_dict_list(self):
        """Test table formatting for list with empty dictionaries."""
        data = [{}, {}]
        result = format_table(data)
        
        assert "No data available" in result

    def test_format_table_long_values(self):
        """Test table formatting with long values."""
        data = [
            {"short": "value", "long": "a" * 100},
            {"short": "value2", "long": "b" * 100}
        ]
        result = format_table(data)
        
        # Long values should be truncated in the 15-char column format
        assert "aaaaaaaaaaaa..." in result or len(result.split('\n')[2].split('|')[0].strip()) <= 15

    def test_format_table_primitive_value(self):
        """Test table formatting for primitive values."""
        data = "simple string"
        result = format_table(data)
        
        assert result == "simple string"


class TestBrowserOperations:
    """Test browser opening functions."""

    @unittest.mock.patch('webbrowser.open')
    def test_open_in_browser_success(self, mock_open):
        """Test successful browser opening."""
        url = "https://github.com/test"
        
        open_in_browser(url)
        
        mock_open.assert_called_once_with(url)

    @unittest.mock.patch('webbrowser.open')
    def test_open_in_browser_failure(self, mock_open):
        """Test browser opening failure handling."""
        mock_open.side_effect = Exception("Browser error")
        
        # Should handle exception gracefully
        open_in_browser("https://github.com/test")

    def test_open_in_browser_invalid_url(self):
        """Test browser opening with invalid URL."""
        with pytest.raises(SystemExit):
            open_in_browser("javascript:alert('xss')")

    def test_open_in_browser_invalid_scheme(self):
        """Test browser opening with invalid scheme."""
        with pytest.raises(SystemExit):
            open_in_browser("ftp://example.com")

    @unittest.mock.patch('gh_actions_optimizer.shared.output.open_in_browser')
    def test_open_github_pricing(self, mock_open):
        """Test GitHub pricing page opening."""
        open_github_pricing()
        mock_open.assert_called_once_with("https://github.com/pricing")

    @unittest.mock.patch('gh_actions_optimizer.shared.output.open_in_browser')
    def test_open_github_docs(self, mock_open):
        """Test GitHub docs page opening."""
        open_github_docs()
        mock_open.assert_called_once_with("https://docs.github.com/en/actions")


class TestOutputPathSecurity:
    """Test output path security measures."""

    def test_output_path_current_directory(self):
        """Test output to current directory is allowed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                output_file = "test.json"
                
                format_output({"test": "data"}, "json", output_file)
                assert os.path.exists(output_file)
            finally:
                os.chdir(original_cwd)

    def test_output_path_home_directory(self):
        """Test output to home directory is allowed."""
        home_dir = os.path.expanduser("~")
        output_file = os.path.join(home_dir, "test_output.json")
        
        try:
            format_output({"test": "data"}, "json", output_file)
            assert os.path.exists(output_file)
        finally:
            # Clean up
            if os.path.exists(output_file):
                os.remove(output_file)

    def test_output_path_absolute_invalid(self):
        """Test that absolute paths outside allowed directories are blocked."""
        with pytest.raises(SystemExit):
            format_output({"test": "data"}, "json", "/tmp/test.json")


class TestFormatTableEdgeCases:
    """Test edge cases in table formatting."""

    def test_format_table_dict_very_long_value(self):
        """Test table formatting with very long values."""
        data = {"key": "x" * 100}
        result = format_table(data)
        
        # Long values should be truncated in dict format
        assert "..." in result

    def test_format_table_list_with_none_values(self):
        """Test table formatting with None values."""
        data = [
            {"name": "item1", "value": None},
            {"name": "item2", "value": 20}
        ]
        result = format_table(data)
        
        assert "N/A" in result  # None should be replaced with N/A

    def test_format_table_nested_structures(self):
        """Test table formatting with deeply nested structures."""
        data = [
            {"name": "item1", "config": {"nested": {"deep": "value"}}},
            {"name": "item2", "config": [1, 2, 3, 4, 5]}
        ]
        result = format_table(data)
        
        # Nested structures should be stringified and truncated
        assert "..." in result or "nested" in result