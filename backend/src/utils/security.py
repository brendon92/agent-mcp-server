import os
import sys
import pathlib
import tempfile
import logging
from contextlib import contextmanager
from typing import Generator, Union

logger = logging.getLogger(__name__)

# Default max file size: 10MB
DEFAULT_MAX_BYTES = 10 * 1024 * 1024

class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass

class QuotaExceededError(SecurityError):
    """Raised when a file size quota is exceeded."""
    pass

class BoxedPath:
    """
    A secure path abstraction that ensures all operations are confined within
    a specific root directory (sandbox).
    
    Features:
    - Path traversal prevention
    - Symlink escape detection (via realpath)
    - Audit logging
    """
    def __init__(self, path: Union[str, pathlib.Path], root_dir: Union[str, pathlib.Path]):
        self.root_dir = pathlib.Path(root_dir).resolve()
        if not self.root_dir.is_absolute():
            raise ValueError(f"Root directory must be absolute: {self.root_dir}")
        
        path_obj = pathlib.Path(path)
        
        # Re-root absolute paths to sandbox
        if path_obj.is_absolute():
            if not str(path_obj).startswith(str(self.root_dir)):
                # Treat as relative to sandbox root
                clean_path = str(path).lstrip(os.sep)
                self.full_path = (self.root_dir / clean_path).resolve()
            else:
                self.full_path = path_obj.resolve()
        else:
            self.full_path = (self.root_dir / path).resolve()

        self.validate()
        
        # Audit hook
        sys.audit("mcp.filesystem.boxedpath", str(self.full_path), str(self.root_dir))

    def validate(self):
        """
        Validates that the resolved path is strictly within the root directory.
        Uses os.path.realpath for symlink resolution.
        """
        # Use realpath for robust symlink resolution
        try:
            real_path = os.path.realpath(self.full_path)
            real_root = os.path.realpath(self.root_dir)
        except OSError as e:
            raise SecurityError(f"Path resolution failed: {e}")
        
        # Check containment
        if not real_path.startswith(real_root + os.sep) and real_path != real_root:
            raise SecurityError(
                f"Access denied: Path '{self.full_path}' resolves to '{real_path}', "
                f"which is outside sandbox '{real_root}'"
            )
        
        # Handle non-existent files (for write operations)
        if not os.path.exists(self.full_path):
            parent_real = os.path.realpath(os.path.dirname(self.full_path))
            if not parent_real.startswith(real_root + os.sep) and parent_real != real_root:
                raise SecurityError(f"Access denied: Parent directory is outside sandbox")

    def __str__(self):
        return str(self.full_path)

    def exists(self) -> bool:
        return self.full_path.exists()

    def is_file(self) -> bool:
        return self.full_path.is_file()

    def is_dir(self) -> bool:
        return self.full_path.is_dir()
    
    def mkdir(self, parents=False, exist_ok=False):
        sys.audit("mcp.filesystem.mkdir", str(self.full_path))
        self.full_path.mkdir(parents=parents, exist_ok=exist_ok)

@contextmanager
def atomic_writer(
    path: BoxedPath, 
    mode: str = "w", 
    encoding: str = "utf-8",
    max_bytes: int = DEFAULT_MAX_BYTES
) -> Generator:
    """
    Context manager for atomic file writes with size quota.
    
    Args:
        path: BoxedPath target
        mode: File mode ('w' or 'wb')
        encoding: Text encoding (ignored for binary)
        max_bytes: Maximum allowed file size (default 10MB)
    """
    if "b" in mode:
        encoding = None
        
    target_path = path.full_path
    parent_dir = target_path.parent
    
    if not parent_dir.exists():
        raise FileNotFoundError(f"Directory does not exist: {parent_dir}")

    # Audit hook
    sys.audit("mcp.filesystem.write", str(target_path), max_bytes)
    
    tmp_fd, tmp_path = tempfile.mkstemp(dir=parent_dir, text="b" not in mode)
    bytes_written = 0
    
    class QuotaEnforcedFile:
        """Wrapper that enforces write quota."""
        def __init__(self, fd, max_bytes):
            self._fd = fd
            self._max_bytes = max_bytes
            self._written = 0
            
        def write(self, data):
            if isinstance(data, str):
                data_bytes = len(data.encode('utf-8'))
            else:
                data_bytes = len(data)
            
            if self._written + data_bytes > self._max_bytes:
                raise QuotaExceededError(
                    f"Write quota exceeded: {self._written + data_bytes} > {self._max_bytes} bytes"
                )
            
            self._written += data_bytes
            return self._fd.write(data)
        
        def flush(self):
            self._fd.flush()
            
        def fileno(self):
            return self._fd.fileno()
    
    try:
        with os.fdopen(tmp_fd, mode, encoding=encoding) as f:
            quota_file = QuotaEnforcedFile(f, max_bytes)
            yield quota_file
            f.flush()
            os.fsync(f.fileno())
            
        os.replace(tmp_path, target_path)
        logger.info(f"AUDIT: Atomic write to {target_path}")
        
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

