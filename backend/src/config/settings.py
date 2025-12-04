import os
import yaml
from typing import List, Dict, Any, Literal

class ServerConfig:
    workspace_dir: str = os.environ.get("MCP_WORKSPACE_DIR", "./test_workspace")
    enable_integrations: bool = True
    
    # Per-category toggle
    enabled_categories: List[str] = [
        "web_search",
        "browser",
        "filesystem", 
        "execution",
        "tool_management",
        "utilities",
        "command",
        "database",
        "developer",
        "vcs"
    ]
    
    # Security
    sandbox_enabled: bool = True
    max_tool_execution_time: int = 30
    
    _instance = None
    _config_data: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> "ServerConfig":
        if cls._instance is None:
            cls._instance = ServerConfig()
        return cls._instance

    @classmethod
    def from_yaml(cls, path: str) -> "ServerConfig":
        """Load configuration from a YAML file and return a ServerConfig instance."""
        instance = cls()
        instance.load_from_yaml(path)
        return instance

    def load_from_yaml(self, path: str) -> None:
        """Load configuration from a YAML file."""
        if not os.path.exists(path):
            return
            
        with open(path, 'r') as f:
            self._config_data = yaml.safe_load(f) or {}
            
    def get_integration_config(self, category: str, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific integration provider."""
        if not self._config_data:
            return {}
            
        category_config = self._config_data.get(category, {})
        if not category_config.get("enabled", True):
            return {"enabled": False}
            
        provider_config = category_config.get("providers", {}).get(provider, {})
        # Merge with defaults if needed, for now just return provider config
        # Ensure enabled status is respected
        if not provider_config.get("enabled", False):
             return {"enabled": False}
             
        return provider_config
