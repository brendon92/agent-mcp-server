from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class MCPIntegration(ABC):
    """Base class for all third-party MCP server integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.category: str = ""
        self.name: str = ""
        
    @abstractmethod
    async def initialize(self) -> None:
        """Start/connect to external server"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup resources"""
        pass
    
    @abstractmethod
    def list_tools(self) -> List[Dict[str, Any]]:
        """Return available tools from this integration"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool"""
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if integration can be used"""
        return True
