"""Output formatting and web browser utilities."""

import json
import sys
import webbrowser
from typing import Any, Optional

import yaml

from .cli import log_error, log_info


def format_output(
    data: Any, format_type: str = "table", output_file: Optional[str] = None
) -> None:
    """Format and output data in the specified format."""
    if format_type == "json":
        output = json.dumps(data, indent=2)
    elif format_type == "yaml":
        output = yaml.dump(data, default_flow_style=False)
    else:  # table format
        output = format_table(data)

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)
            log_info(f"Output written to {output_file}")
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
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
            else:
                value_str = str(value)
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
                        if len(value_str) > 15:
                            value_str = value_str[:12] + "..."
                    else:
                        value_str = str(value)[:15]
                    row_values.append(f"{value_str:<15}")
                rows.append(" | ".join(row_values))

            return f"{header}\n{separator}\n" + "\n".join(rows)
        else:
            return "\n".join(str(item) for item in data)
    else:
        return str(data)


def open_in_browser(url: str) -> None:
    """Open URL in web browser."""
    try:
        webbrowser.open(url)
        log_info(f"Opened {url} in web browser")
    except Exception as e:
        log_error(f"Failed to open browser: {e}")
        log_info(f"Please manually visit: {url}")


def open_github_pricing() -> None:
    """Open GitHub Actions pricing page."""
    open_in_browser("https://github.com/pricing")


def open_github_docs() -> None:
    """Open GitHub Actions documentation."""
    open_in_browser("https://docs.github.com/en/actions")
