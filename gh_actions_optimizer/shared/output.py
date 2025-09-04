"""Output formatting and web browser utilities."""

import json
import os
import sys
import webbrowser
from typing import Any, Optional

import yaml

from .cli import log_error, log_info
from .validation import InputValidator, validate_and_log_error


def format_output(
    data: Any, format_type: str = "table", output_file: Optional[str] = None
) -> None:
    """Format and output data in the specified format with enhanced security."""
    if format_type == "json":
        output = json.dumps(data, indent=2, ensure_ascii=True)
    elif format_type == "yaml":
        output = yaml.dump(data, default_flow_style=False, allow_unicode=False)
    else:  # table format
        output = format_table(data)

    if output_file:
        # Validate output file path for security
        validate_and_log_error(InputValidator.validate_file_path, output_file, True)
        validate_and_log_error(InputValidator.validate_filename, 
                             os.path.basename(output_file))
        
        # Additional security checks
        abs_path = os.path.abspath(output_file)
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        
        # Allow temp directories for testing
        allowed_paths = [cwd, home]
        import tempfile
        allowed_paths.append(tempfile.gettempdir())
        
        if not any(abs_path.startswith(path) for path in allowed_paths):
            log_error("Output file must be in current directory, user home directory, or temp directory")
            sys.exit(1)
        
        try:
            # Create directory if it doesn't exist (securely)
            output_dir = os.path.dirname(abs_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, mode=0o750, exist_ok=True)
                
            # Write file with secure permissions
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(output)
            
            # Set secure file permissions
            os.chmod(abs_path, 0o640)
            log_info(f"Output written to {abs_path}")
        except OSError as e:
            log_error(f"Failed to write output file: {e}")
            sys.exit(1)
    else:
        print(output)


def format_table(data: Any) -> str:
    """Format data as a simple table."""
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value_str = str(value)
                if len(value_str) > 47:  # 50 - 3 for "..."
                    value_str = value_str[:47] + "..."
            else:
                value_str = str(value)
                if len(value_str) > 47:
                    value_str = value_str[:47] + "..."
            lines.append(f"{key:<30} {value_str}")
        return "\n".join(lines)
    elif isinstance(data, list):
        if not data:
            return "No items found"

        # Try to format as table if items are dictionaries
        if all(isinstance(item, dict) for item in data):
            if not data:
                return "No items found"

            # Get all unique keys
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())

            if not all_keys:
                return "No data available"

            sorted_keys = sorted(all_keys)

            # Create header
            header = " | ".join(f"{key:<15}" for key in sorted_keys)
            separator = "-" * len(header)

            # Create rows
            rows = []
            for item in data:
                row_values = []
                for key in sorted_keys:
                    value = item.get(key, "N/A")
                    if isinstance(value, (dict, list)):
                        value_str = str(value)
                        if len(value_str) > 12:  # 15 - 3 for "..."
                            value_str = value_str[:12] + "..."
                    else:
                        value_str = str(value) if value is not None else "N/A"
                        if len(value_str) > 15:
                            value_str = value_str[:12] + "..."
                    row_values.append(f"{value_str:<15}")
                rows.append(" | ".join(row_values))

            return f"{header}\n{separator}\n" + "\n".join(rows)
        else:
            return "\n".join(str(item) for item in data)
    else:
        return str(data)


def open_in_browser(url: str) -> None:
    """Open URL in web browser."""
    # Validate URL for security
    validated_url = validate_and_log_error(
        InputValidator.validate_url, 
        url, 
        ["https", "http"]
    )
    
    try:
        webbrowser.open(validated_url)
        log_info(f"Opened {validated_url} in web browser")
    except Exception as e:
        log_error(f"Failed to open browser: {e}")
        log_info(f"Please manually visit: {validated_url}")


def open_github_pricing() -> None:
    """Open GitHub Actions pricing page."""
    open_in_browser("https://github.com/pricing")


def open_github_docs() -> None:
    """Open GitHub Actions documentation."""
    open_in_browser("https://docs.github.com/en/actions")
