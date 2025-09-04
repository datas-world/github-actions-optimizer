"""Comprehensive input validation and sanitization utilities."""

import os
import re
import stat
import sys
import tempfile
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class InputValidator:
    """Comprehensive input validator for security-critical operations."""

    # Security patterns - optimized to prevent ReDoS vulnerabilities
    DANGEROUS_PATTERNS = [
        r"\.\.[/\\]",  # Directory traversal (atomic pattern)
        r"\$\{[^}]{0,50}\}",  # Variable injection (reduced limit for safety)
        r"(?i)(?:script|javascript|vbscript):",  # Script injection (atomic alternation)
        r"(?i)<script[>\s]",  # HTML script tags (opening)
        r"(?i)eval\s*\(",  # Code evaluation (atomic)
        r"(?i)exec\s*\(",  # Code execution (atomic)
        r"(?i)system\s*\(",  # System calls (atomic)
        r"(?i)import\s+os\b",  # OS module imports (word boundary)
        r"(?i)__import__",  # Dynamic imports (literal match)
        r"(?i)subprocess\.",  # Subprocess usage (literal dot)
        r"(?i)os\.system",  # OS system calls (escaped dot)
    ]

    # GitHub-specific patterns (optimized for security and performance)
    GITHUB_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9._-]{0,98}[a-zA-Z0-9])?/[a-zA-Z0-9](?:[a-zA-Z0-9._-]{0,98}[a-zA-Z0-9])?$")
    GITHUB_REF_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]{1,200}$")  # Reduced limit for safety
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
        """Validate environment variable name and value with enhanced security."""
        if not name or not isinstance(name, str):
            raise ValidationError("Environment variable name cannot be empty")

        if not isinstance(value, str):
            raise ValidationError("Environment variable value must be a string")

        name = name.strip()
        
        # Validate name format (alphanumeric and underscore only, must start with letter/underscore)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise ValidationError(
                "Invalid environment variable name format. Must start with letter or underscore, "
                "followed by alphanumeric characters or underscores"
            )

        # Check for reserved/dangerous environment variable names in specific contexts
        # Only block these in untrusted contexts, not in normal validation
        critical_env_names = {
            "LD_PRELOAD", "IFS"  # Only the most critical ones
        }
        
        if name.upper() in critical_env_names:
            raise ValidationError(f"Environment variable '{name}' is considered dangerous")

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

        # Additional checks for control characters and null bytes
        if any(ord(char) < 32 for char in value) or '\x00' in value:
            raise ValidationError(
                "Environment variable value contains control characters or null bytes"
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

        # Check for dangerous shell characters and patterns (optimized for security)
        dangerous_chars = r'[;&|`$(){}<>*?[\]~]'
        if re.search(dangerous_chars, value):
            raise ValidationError(
                "Value contains characters not safe for shell execution"
            )

        # Additional checks for shell injection patterns (ReDoS-safe)
        shell_patterns = [
            r"(?i)\beval\b",        # Word boundary prevents partial matches
            r"(?i)\bexec\b",        # Word boundary prevents partial matches
            r"(?i)\bsystem\b",      # Word boundary prevents partial matches
            r"(?i)\bpopen\b",       # Word boundary prevents partial matches
            r"\\x[0-9a-fA-F]{2}",   # Hex escape sequences (case insensitive, limited)
            r"\\[0-7]{1,3}",        # Octal escape sequences (limited range)
        ]
        
        for pattern in shell_patterns:
            if re.search(pattern, value):
                raise ValidationError(
                    "Value contains shell injection patterns"
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
        """Validate file size with enhanced security."""
        try:
            path = Path(file_path)
            
            # Validate path security first
            resolved_path = path.resolve()
            if not resolved_path.exists():
                raise ValidationError(f"File does not exist: {file_path}")

            # Check if file is readable and not a special file
            if not resolved_path.is_file():
                raise ValidationError(f"Path is not a regular file: {file_path}")

            size = resolved_path.stat().st_size
            if size > max_size_bytes:
                raise ValidationError(
                    f"File too large: {size} bytes (max {max_size_bytes} bytes)"
                )
        except OSError as e:  # nosec B110 - Proper exception handling for file operations
            raise ValidationError(f"Cannot access file: {e}")

    @classmethod
    def create_secure_temp_file(cls, suffix: str = "", prefix: str = "temp_") -> str:
        """Create a secure temporary file with proper permissions."""
        import tempfile
        import stat
        
        # Validate inputs
        if not isinstance(suffix, str) or len(suffix) > 20:
            raise ValidationError("Invalid suffix for temporary file")
        if not isinstance(prefix, str) or len(prefix) > 20:
            raise ValidationError("Invalid prefix for temporary file")
            
        # Create secure temporary file
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        try:
            # Set secure file permissions (owner read/write only)
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)  # 600 permissions
            os.close(fd)
            return temp_path
        except OSError as e:
            # Clean up on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise ValidationError(f"Cannot create secure temporary file: {e}")

    @classmethod
    def validate_yaml_content(cls, content: str, max_size: int = 1024 * 1024) -> Dict[str, Any]:
        """Safely validate and parse YAML content."""
        if not content or not isinstance(content, str):
            raise ValidationError("YAML content must be a non-empty string")
            
        if len(content) > max_size:
            raise ValidationError(f"YAML content too large (max {max_size} bytes)")
            
        # Check for dangerous patterns in YAML content
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                raise ValidationError("YAML content contains potentially dangerous patterns")
        
        try:
            # Use safe_load to prevent code execution
            parsed = yaml.safe_load(content)
            if parsed is None:
                raise ValidationError("YAML content is empty or invalid")
            if not isinstance(parsed, dict):
                raise ValidationError("YAML content must be a dictionary")
            return parsed
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML content: {e}")

    @classmethod  
    def validate_network_url(cls, url: str) -> str:
        """Validate URL for network operations with enhanced security."""
        validated_url = cls.validate_url(url, ["https"])  # Only allow HTTPS
        
        parsed = urlparse(validated_url)
        
        # Only allow GitHub domains for security
        allowed_domains = [
            "github.com",
            "api.github.com", 
            "raw.githubusercontent.com",
            "codeload.github.com"
        ]
        
        if parsed.hostname not in allowed_domains:
            raise ValidationError(
                f"Domain '{parsed.hostname}' not allowed for network operations. "
                f"Allowed domains: {allowed_domains}"
            )
            
        return validated_url


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