import os
import yaml
from typing import List, Dict, Any, Optional
from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings

class ProviderConfig(BaseModel):
    enabled: bool = False
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    # Allow extra fields for specific provider configs
    class Config:
        extra = "allow"

class CategoryConfig(BaseModel):
    enabled: bool = True
    providers: Dict[str, ProviderConfig] = {}

class ServerConfig(BaseSettings):
    """
    Application Configuration based on Pydantic BaseSettings.
    Reads from environment variables and optional YAML config.
    """
    workspace_dir: str = Field(default="./test_workspace", description="Path to the workspace directory")
    # Security
    auth_token: str = Field(..., description="Authentication token (Required)")
    sandbox_enabled: bool = True
    max_tool_execution_time: int = 30
    
    # Feature Flags
    enable_integrations: bool = True
    
    # Integration Configs (loaded from YAML typically)
    integrations: Dict[str, CategoryConfig] = {}
    
    class Config:
        env_prefix = "MCP_"
        case_sensitive = False
        extra = "ignore" # Ignore unknown env vars

    @classmethod
    def from_yaml(cls, path: str) -> "ServerConfig":
        """Load configuration from a YAML file and environment variables."""
        
        yaml_data = {}
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    # Flatten: The YAML contains root keys like workspace_dir
                    yaml_data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config from {path}: {e}")
        
        # We pass YAML data as init args. Pydantic BaseSettings will merge with Env vars.
        # Note: By default BaseSettings only uses env vars if value is NOT passed in init.
        # So YAML takes precedence over Env? 
        # Actually usually Env should take precedence in 12-factor apps.
        # But here we pass kwargs, which override everything.
        # To make Env override YAML, we should not pass keys that are in Env?
        # Or let BaseSettings process things.
        
        # A simple way: Load settings from Env first, then update with YAML (if we want YAML to override)
        # OR Load from YAML, then override with Env.
        
        # Proper way with Pydantic:
        # 1. Create instance (reads env).
        # 2. Update with YAML? No, immutability issues if frozen.
        
        # Let's trust that the user won't conflict or we define priority.
        # For now, simplistic approach: passing kwargs overrides env.
        # If we want Env > YAML, we should remove keys from yaml_data if they exist in os.environ.
        
        for key in list(yaml_data.keys()):
            env_key = f"MCP_{key.upper()}"
            if env_key in os.environ:
                del yaml_data[key]
                
        return cls(**yaml_data)

    def get_integration_config(self, category: str, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific integration provider."""
        cat_config = self.integrations.get(category)
        if not cat_config or not cat_config.enabled:
            return {"enabled": False}
            
        prov_config = cat_config.providers.get(provider)
        if not prov_config or not prov_config.enabled:
             return {"enabled": False}
             
        return prov_config.model_dump(exclude_none=True)

