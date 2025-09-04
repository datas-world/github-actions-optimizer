"""Comprehensive input validation and sanitization utilities."""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class InputValidator:
    """Comprehensive input validator for security-critical operations."""

    # Security patterns
    DANGEROUS_PATTERNS = [
        r"\.\.\/",  # Directory traversal
        r"\.\.\\",  # Windows directory traversal
        r"\$\{.*\}",  # Variable injection
        r"(?i)(script|javascript|vbscript):",  # Script injection
        r"(?i)<script",  # HTML script tags
        r"(?i)eval\s*\(",  # Code evaluation
        r"(?i)exec\s*\(",  # Code execution
        r"(?i)system\s*\(",  # System calls
        r"(?i)import\s+os",  # OS module imports
        r"(?i)__import__",  # Dynamic imports
    ]

    # GitHub-specific patterns
    GITHUB_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?/[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$")
    GITHUB_REF_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]+$")
    COMMIT_SHA_PATTERN = re.compile(r"^[a-f0-9]{7,40}$")
    
    # Input limits
    MAX_REPO_LENGTH = 100
    MAX_PATH_LENGTH = 4096
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB
    MAX_FILENAME_LENGTH = 255
    MAX_ENV_VAR_LENGTH = 4096

    @classmethod
    def validate_repository_name(cls, repo: str) -> str:
        """Validate GitHub repository name format."""
        if not repo or not isinstance(repo, str):
            raise ValidationError("Repository name cannot be empty")

        repo = repo.strip()
        
        if len(repo) > cls.MAX_REPO_LENGTH:
            raise ValidationError(
                f"Repository name too long (max {cls.MAX_REPO_LENGTH} characters)"
            )

        if not cls.GITHUB_REPO_PATTERN.match(repo):
            raise ValidationError(
                "Invalid repository format. Expected: owner/repo"
            )

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, repo):
                raise ValidationError(
                    f"Repository name contains potentially dangerous pattern"
                )

        return repo

    @classmethod
    def validate_file_path(cls, path: str, allow_absolute: bool = False) -> str:
        """Validate and sanitize file paths to prevent directory traversal."""
        if not path or not isinstance(path, str):
            raise ValidationError("File path cannot be empty")

        path = path.strip()
        
        if len(path) > cls.MAX_PATH_LENGTH:
            raise ValidationError(
                f"File path too long (max {cls.MAX_PATH_LENGTH} characters)"
            )

        # Check for directory traversal patterns
        if ".." in path:
            raise ValidationError("Directory traversal not allowed in file paths")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path):
                raise ValidationError(
                    "File path contains potentially dangerous pattern"
                )

        # Normalize path
        normalized_path = os.path.normpath(path)
        
        # Ensure path doesn't escape intended directory
        if not allow_absolute and os.path.isabs(normalized_path):
            raise ValidationError("Absolute paths not allowed")

        # Additional check for Windows UNC paths
        if normalized_path.startswith("\\\\"):
            raise ValidationError("UNC paths not allowed")

        return normalized_path

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate filename for security and compatibility."""
        if not filename or not isinstance(filename, str):
            raise ValidationError("Filename cannot be empty")

        filename = filename.strip()
        
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            raise ValidationError(
                f"Filename too long (max {cls.MAX_FILENAME_LENGTH} characters)"
            )

        # Check for null bytes
        if "\x00" in filename:
            raise ValidationError("Null bytes not allowed in filename")

        # Check for control characters
        if any(ord(char) < 32 for char in filename):
            raise ValidationError("Control characters not allowed in filename")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, filename):
                raise ValidationError(
                    "Filename contains potentially dangerous pattern"
                )

        # Check for reserved names on Windows
        reserved_names = {
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        }
        
        base_name = filename.split(".")[0].upper()
        if base_name in reserved_names:
            raise ValidationError(f"'{filename}' is a reserved filename")

        return filename

    @classmethod
    def validate_yaml_content(cls, content: str) -> Dict[str, Any]:
        """Validate and parse YAML content safely."""
        if not content or not isinstance(content, str):
            raise ValidationError("YAML content cannot be empty")

        if len(content) > cls.MAX_CONTENT_LENGTH:
            raise ValidationError(
                f"Content too large (max {cls.MAX_CONTENT_LENGTH} bytes)"
            )

        # Check for dangerous patterns in YAML
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                raise ValidationError(
                    "YAML content contains potentially dangerous pattern"
                )

        try:
            # Use safe_load to prevent code execution
            parsed = yaml.safe_load(content)
            if parsed is None:
                raise ValidationError("YAML content is empty or invalid")
            if not isinstance(parsed, dict):
                raise ValidationError("YAML content must be a dictionary")
            return parsed
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML format: {e}")

    @classmethod
    def validate_github_ref(cls, ref: str) -> str:
        """Validate GitHub reference (branch, tag, etc.)."""
        if not ref or not isinstance(ref, str):
            raise ValidationError("GitHub reference cannot be empty")

        ref = ref.strip()
        
        if len(ref) > 250:  # GitHub limit
            raise ValidationError("GitHub reference too long")

        if not cls.GITHUB_REF_PATTERN.match(ref):
            raise ValidationError("Invalid GitHub reference format")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, ref):
                raise ValidationError(
                    "GitHub reference contains potentially dangerous pattern"
                )

        return ref

    @classmethod
    def validate_commit_sha(cls, sha: str) -> str:
        """Validate commit SHA format."""
        if not sha or not isinstance(sha, str):
            raise ValidationError("Commit SHA cannot be empty")

        sha = sha.strip().lower()
        
        if not cls.COMMIT_SHA_PATTERN.match(sha):
            raise ValidationError("Invalid commit SHA format")

        return sha

    @classmethod
    def validate_environment_variable(cls, name: str, value: str) -> tuple[str, str]:
        """Validate environment variable name and value."""
        if not name or not isinstance(name, str):
            raise ValidationError("Environment variable name cannot be empty")

        if not isinstance(value, str):
            raise ValidationError("Environment variable value must be a string")

        name = name.strip()
        
        # Validate name format (alphanumeric and underscore only)
        if not re.match(r"^[A-Z_][A-Z0-9_]*$", name):
            raise ValidationError(
                "Invalid environment variable name format"
            )

        if len(value) > cls.MAX_ENV_VAR_LENGTH:
            raise ValidationError(
                f"Environment variable value too long (max {cls.MAX_ENV_VAR_LENGTH} characters)"
            )

        # Check for dangerous patterns in value
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value):
                raise ValidationError(
                    "Environment variable value contains potentially dangerous pattern"
                )

        return name, value

    @classmethod
    def validate_url(cls, url: str, allowed_schemes: Optional[List[str]] = None) -> str:
        """Validate URL format and scheme."""
        if not url or not isinstance(url, str):
            raise ValidationError("URL cannot be empty")

        url = url.strip()
        
        if allowed_schemes is None:
            allowed_schemes = ["https", "http"]

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {e}")

        if parsed.scheme not in allowed_schemes:
            raise ValidationError(
                f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}"
            )

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, url):
                raise ValidationError(
                    "URL contains potentially dangerous pattern"
                )

        return url

    @classmethod
    def validate_input_length(cls, value: str, max_length: int, name: str = "Input") -> str:
        """Validate input length."""
        if not isinstance(value, str):
            raise ValidationError(f"{name} must be a string")

        if len(value) > max_length:
            raise ValidationError(
                f"{name} too long (max {max_length} characters)"
            )

        return value

    @classmethod
    def sanitize_for_shell(cls, value: str) -> str:
        """Sanitize value for safe shell usage."""
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")

        # Remove or escape dangerous shell characters
        dangerous_chars = r'[;&|`$(){}<>]'
        if re.search(dangerous_chars, value):
            raise ValidationError(
                "Value contains characters not safe for shell execution"
            )

        return value

    @classmethod
    def validate_file_extension(cls, filename: str, allowed_extensions: List[str]) -> str:
        """Validate file extension against allowed list."""
        if not filename or not isinstance(filename, str):
            raise ValidationError("Filename cannot be empty")

        filename = filename.lower()
        
        if not any(filename.endswith(ext.lower()) for ext in allowed_extensions):
            raise ValidationError(
                f"File extension not allowed. Allowed: {allowed_extensions}"
            )

        return filename

    @classmethod
    def validate_file_size(cls, file_path: Union[str, Path], max_size_bytes: int) -> None:
        """Validate file size."""
        try:
            path = Path(file_path)
            if not path.exists():
                raise ValidationError(f"File does not exist: {file_path}")

            size = path.stat().st_size
            if size > max_size_bytes:
                raise ValidationError(
                    f"File too large: {size} bytes (max {max_size_bytes} bytes)"
                )
        except OSError as e:
            raise ValidationError(f"Cannot access file: {e}")


def validate_and_log_error(validation_func: Any, *args: Any, **kwargs: Any) -> Any:
    """Helper to validate input and log errors appropriately."""
    try:
        return validation_func(*args, **kwargs)
    except ValidationError as e:
        # Import here to avoid circular imports
        from .cli import log_error
        log_error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        # Import here to avoid circular imports  
        from .cli import log_error
        log_error(f"Unexpected validation error: {e}")
        sys.exit(1)