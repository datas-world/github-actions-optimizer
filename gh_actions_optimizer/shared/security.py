"""Security utilities for handling sensitive data and secrets."""

import re
from typing import Any, Dict, List, Pattern


class SecuritySanitizer:
    """Sanitize sensitive data from logs, errors, and outputs."""

    def __init__(self) -> None:
        """Initialize security sanitizer with patterns for sensitive data."""
        self._patterns: List[Pattern[str]] = [
            # GitHub tokens (classic and fine-grained) - more precise patterns
            re.compile(r"gh[psu]_[A-Za-z0-9_]{36,255}", re.IGNORECASE),
            # Classic GitHub tokens (40 hex chars, when preceded by token-related words)
            re.compile(
                r"(?:token|password|secret|key|auth)[\s:=]+[a-f0-9]{40}\b",
                re.IGNORECASE,
            ),
            # Generic Bearer tokens
            re.compile(r"Bearer\s+[A-Za-z0-9._\-~+/]+=*", re.IGNORECASE),
            # Authorization headers
            re.compile(r"Authorization:\s*[^\s\n]+", re.IGNORECASE),
            # URLs with embedded tokens
            re.compile(
                r"https://[^@\s]*:[^@\s]*@[^\s]*", re.IGNORECASE
            ),  # URLs with credentials
            re.compile(
                r"https://[^?\s]*\?[^=\s]*token[^=\s]*=[^&\s]*", re.IGNORECASE
            ),  # URLs with token params
            # SSH keys (RSA, ECDSA, ED25519)
            re.compile(
                r"-----BEGIN[^-]*PRIVATE KEY-----[^-]*-----END[^-]*PRIVATE KEY-----",
                re.DOTALL,
            ),
            # AWS credentials
            re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),
            # Other common secret patterns - more conservative
            re.compile(
                r"(?:password|passwd|secret|token)[\s:=]+['\"]?[^\s'\"]+", re.IGNORECASE
            ),
        ]

    def sanitize_text(self, text: str) -> str:
        """Sanitize sensitive data from text."""
        if not text:
            return text

        sanitized = text
        for pattern in self._patterns:
            sanitized = pattern.sub("[REDACTED]", sanitized)

        return sanitized

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from dictionary recursively."""
        if not isinstance(data, dict):
            return data  # type: ignore[unreachable]

        sanitized: Dict[str, Any] = {}
        for key, value in data.items():
            # Check if key suggests sensitive data - be more specific
            key_lower = key.lower()
            is_sensitive = (
                key_lower
                in [
                    "token",
                    "password",
                    "secret",
                    "key",
                    "auth",
                    "credential",
                    "private",
                    "passwd",
                    "authorization",
                    "bearer",
                ]
                or key_lower.endswith("_token")
                or key_lower.endswith("_password")
                or key_lower.endswith("_secret")
                or key_lower.endswith("_auth")
                or key_lower.endswith("_credential")
                or key_lower.startswith("token_")
                or key_lower.startswith("password_")
                or key_lower.startswith("secret_")
                or key_lower.startswith("auth_")
                or "github_token" in key_lower
                or "api_key" in key_lower
                or "access_token" in key_lower
            )

            if is_sensitive:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    (
                        self.sanitize_text(item)
                        if isinstance(item, str)
                        else (
                            self.sanitize_dict(item) if isinstance(item, dict) else item
                        )
                    )
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def is_sensitive_key(self, key: str) -> bool:
        """Check if a key name suggests sensitive data."""
        sensitive_keywords = [
            "token",
            "password",
            "secret",
            "key",
            "auth",
            "credential",
            "private",
            "passwd",
            "authorization",
            "bearer",
        ]
        return any(
            key.lower() == keyword
            or key.lower().endswith("_" + keyword)
            or key.lower().startswith(keyword + "_")
            or "_" + keyword + "_" in key.lower()
            for keyword in sensitive_keywords
        )


# Global sanitizer instance
_sanitizer = SecuritySanitizer()


def sanitize_for_logging(message: str) -> str:
    """Sanitize a message for safe logging."""
    return _sanitizer.sanitize_text(message)


def sanitize_error_message(error_message: str) -> str:
    """Sanitize error message to prevent sensitive data exposure."""
    return _sanitizer.sanitize_text(error_message)


def sanitize_subprocess_output(output: str, command_args: List[str]) -> str:
    """Sanitize subprocess output considering the command that was run."""
    # First apply general sanitization
    sanitized = _sanitizer.sanitize_text(output)

    # Additional sanitization based on command type
    if any("auth" in arg for arg in command_args):
        # For auth-related commands, be extra cautious
        sanitized = re.sub(
            r"token:\s*[^\s\n]+", "token: [REDACTED]", sanitized, flags=re.IGNORECASE
        )
        sanitized = re.sub(
            r"user:\s*[^\s\n]+", "user: [REDACTED]", sanitized, flags=re.IGNORECASE
        )

    return sanitized


def validate_github_token_format(token: str) -> bool:
    """Validate GitHub token format without logging the token."""
    if not token:
        return False

    # GitHub personal access tokens
    if token.startswith("ghp_") and len(token) >= 40:
        return True

    # GitHub app tokens
    if token.startswith("ghu_") and len(token) >= 40:
        return True

    # GitHub installation tokens
    if token.startswith("ghs_") and len(token) >= 40:
        return True

    # Classic tokens (40 characters, hex)
    if len(token) == 40 and re.match(r"^[a-f0-9]{40}$", token):
        return True

    return False


def get_secure_env_var(var_name: str, default: str = "") -> str:
    """Get environment variable value without logging it."""
    import os

    value = os.environ.get(var_name, default)
    # Never log the actual value, even in debug mode
    return value


def mask_repository_url(url: str) -> str:
    """Mask sensitive parts of repository URLs."""
    if not url:
        return url

    # Mask embedded credentials in URLs
    url = re.sub(r"://[^@/]*@", "://[REDACTED]@", url)

    # Mask token parameters
    url = re.sub(r"([?&]token=)[^&]*", r"\1[REDACTED]", url, flags=re.IGNORECASE)
    url = re.sub(r"([?&]access_token=)[^&]*", r"\1[REDACTED]", url, flags=re.IGNORECASE)

    return url
