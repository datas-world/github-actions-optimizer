#!/usr/bin/env python3
"""Sort Java-style properties files by key.

This script sorts .properties files by their keys while preserving comments
and blank lines in their original positions relative to the properties.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple


def parse_properties_file(content: str) -> List[Tuple[str, str, str]]:
    """Parse properties file content into (line_type, key, content) tuples.

    Args:
        content: Raw file content

    Returns:
        List of tuples where:
        - line_type: 'property', 'comment', 'blank'
        - key: property key (empty for non-property lines)
        - content: original line content
    """
    lines = content.splitlines()
    parsed_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Blank line
            parsed_lines.append(("blank", "", line))
        elif stripped.startswith("#"):
            # Comment line
            parsed_lines.append(("comment", "", line))
        elif "=" in stripped:
            # Property line
            key = stripped.split("=", 1)[0].strip()
            parsed_lines.append(("property", key, line))
        else:
            # Treat as comment (lines without = sign)
            parsed_lines.append(("comment", "", line))

    return parsed_lines


def sort_properties_content(content: str) -> str:
    """Sort properties file content by key while preserving structure.

    Args:
        content: Raw file content

    Returns:
        Sorted file content
    """
    parsed_lines = parse_properties_file(content)

    # Group lines into sections (comments/blanks followed by properties)
    sections = []
    current_section_header: List[str] = []
    current_properties: List[Tuple[str, str]] = []

    for line_type, key, line_content in parsed_lines:
        if line_type == "property":
            current_properties.append((key, line_content))
        else:
            # Comment or blank line
            if current_properties:
                # We have accumulated properties, save the section
                sections.append((current_section_header, current_properties))
                current_section_header = []
                current_properties = []
            current_section_header.append(line_content)

    # Handle any remaining properties
    if current_properties:
        sections.append((current_section_header, current_properties))
    elif current_section_header:
        # Only header lines at the end
        sections.append((current_section_header, []))

    # Sort properties within each section and rebuild content
    result_lines = []

    for header_lines, properties in sections:
        # Add header lines (comments/blanks)
        result_lines.extend(header_lines)

        # Sort and add properties
        sorted_properties = sorted(properties, key=lambda x: x[0])
        for _, line_content in sorted_properties:
            result_lines.append(line_content)

    return "\n".join(result_lines)


def sort_properties_file(file_path: Path) -> bool:
    """Sort a properties file in place.

    Args:
        file_path: Path to the properties file

    Returns:
        True if file was modified, False otherwise
    """
    try:
        original_content = file_path.read_text(encoding="utf-8")
        sorted_content = sort_properties_content(original_content)

        # Ensure file ends with newline
        if sorted_content and not sorted_content.endswith("\n"):
            sorted_content += "\n"

        if original_content != sorted_content:
            file_path.write_text(sorted_content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sort properties files by key")
    parser.add_argument("files", nargs="+", type=Path, help="Properties files to sort")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if files are sorted (exit code 1 if not)",
    )

    args = parser.parse_args()

    modified_files = []
    error_count = 0

    for file_path in args.files:
        if not file_path.exists():
            print(f"File not found: {file_path}", file=sys.stderr)
            error_count += 1
            continue

        if not file_path.suffix == ".properties":
            continue  # Skip non-properties files

        try:
            original_content = file_path.read_text(encoding="utf-8")
            sorted_content = sort_properties_content(original_content)

            # Ensure file ends with newline
            if sorted_content and not sorted_content.endswith("\n"):
                sorted_content += "\n"

            if original_content != sorted_content:
                if args.check:
                    print(f"File {file_path} is not sorted")
                    modified_files.append(file_path)
                else:
                    file_path.write_text(sorted_content, encoding="utf-8")
                    print(f"Sorted {file_path}")
                    modified_files.append(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            error_count += 1

    if args.check and modified_files:
        print(f"Found {len(modified_files)} unsorted properties files")
        return 1

    if error_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
