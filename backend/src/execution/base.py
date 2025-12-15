from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ToolExecutor(ABC):
    """
    Abstract base class for executing tools/code.
    Supports different backends (Local, Docker, SSH, etc.)
    """
    
    @abstractmethod
    def execute(self, code: str, timeout: int = 30, env: Optional[Dict[str, str]] = None) -> str:
        """
        Execute the provided code.
        
        Args:
            code: The source code to execute.
            timeout: Execution timeout in seconds.
            env: Environment variables to inject.
            
        Returns:
            The standard output (or error) from the execution.
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Perform any necessary cleanup (e.g., kill containers)."""
        pass
