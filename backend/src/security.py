import os
import re
from typing import Optional

class SecurityError(Exception):
    """Base class for security violations."""
    pass

class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass

class InputValidationError(SecurityError):
    """Raised when input validation fails."""
    pass

def validate_token(token: Optional[str] = None) -> bool:
    """
    Validates the provided token against the MCP_AUTH_TOKEN environment variable.
    
    Args:
        token: The token to validate. If None, checks if the env var is set only.
        
    Returns:
        True if valid.
        
    Raises:
        AuthenticationError: If token is invalid or env var is missing.
    """
    expected_token = os.environ.get("MCP_AUTH_TOKEN")
    if not expected_token:
        raise AuthenticationError("Server misconfiguration: MCP_AUTH_TOKEN not set in environment.")
        
    if token is None:
        # Just checking if env var is set (startup check)
        return True
        
    # Constant time comparison to prevent timing attacks
    if not _constant_time_compare(token, expected_token):
        raise AuthenticationError("Invalid authentication token.")
    
    return True

def _constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time."""
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0

def sanitize_path(path: str, base_dir: str) -> str:
    """
    Sanitizes and validates a file path to prevent directory traversal.
    Ensures the path is within the base_dir.
    
    Args:
        path: The path to sanitize.
        base_dir: The trusted base directory.
        
    Returns:
        Absolute path if safe.
        
    Raises:
        InputValidationError: If path traverses outside base_dir.
    """
    # Resolve absolute paths
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.abspath(os.path.join(abs_base, path))
    
    if not abs_path.startswith(abs_base):
        raise InputValidationError(f"Access denied: Path '{path}' attempts to traverse outside workspace.")
        
    return abs_path

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename to ensure it's safe for use in shell commands or file systems.
    Allowed chars: alphanumeric, dot, dash, underscore.
    
    Args:
        filename: string to sanitize
        
    Returns:
        Sanitized string.
    """
    # Keep only safe characters
    safe = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    if not safe:
        raise InputValidationError("Filename contains no valid characters.")
    return safe
