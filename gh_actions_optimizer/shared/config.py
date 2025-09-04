"""Secure configuration handling utilities."""

import os
from typing import Any, Dict, Optional

from .security import get_secure_env_var, sanitize_for_logging


class SecureConfig:
    """Secure configuration manager that prevents secret exposure."""

    def __init__(self) -> None:
        """Initialize secure configuration manager."""
        self._config: Dict[str, Any] = {}

    def get_github_token(self) -> Optional[str]:
        """Get GitHub token from environment without logging it."""
        # Try different environment variable names for GitHub tokens
        token_vars = [
            "GITHUB_TOKEN",
            "GH_TOKEN", 
            "GITHUB_ACCESS_TOKEN",
        ]
        
        for var in token_vars:
            token = get_secure_env_var(var)
            if token:
                # Log that we found a token but never log the value
                sanitize_for_logging(f"Found GitHub token in environment variable {var}")
                return token
        
        return None

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with secure handling of sensitive data."""
        # Check environment variables first
        env_value = os.environ.get(key.upper(), os.environ.get(key))
        if env_value is not None:
            return env_value
        
        # Check internal config
        return self._config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value

    def validate_required_config(self) -> bool:
        """Validate that required configuration is present."""
        # Check if we have access to GitHub
        token = self.get_github_token()
        if not token:
            return False
        
        return True

    def get_safe_config_summary(self) -> Dict[str, str]:
        """Get a safe summary of configuration for debugging."""
        summary = {}
        
        # Show which environment variables are set (but not their values)
        env_vars_to_check = [
            "GITHUB_TOKEN",
            "GH_TOKEN", 
            "GITHUB_ACCESS_TOKEN",
            "GITHUB_REPOSITORY",
            "GITHUB_ACTOR",
            "GITHUB_WORKFLOW",
        ]
        
        for var in env_vars_to_check:
            if os.environ.get(var):
                summary[var] = "SET"
            else:
                summary[var] = "NOT_SET"
        
        return summary


# Global configuration instance
secure_config = SecureConfig()


def get_github_token() -> Optional[str]:
    """Get GitHub token securely."""
    return secure_config.get_github_token()


def validate_configuration() -> bool:
    """Validate that required configuration is available."""
    return secure_config.validate_required_config()