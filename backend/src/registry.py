import os
import sys
import inspect
import importlib
import logging
from typing import Dict, Any, Callable, List, Optional
from .workspace import Workspace
from .config.settings import ServerConfig
from .integrations.base import MCPIntegration

logger = logging.getLogger(__name__)


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found."""
    pass


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""
    pass


class ToolRegistry:
    def __init__(self, workspace: Workspace, config: ServerConfig = None):
        self.workspace = workspace
        self.config = config or ServerConfig()
        self.system_tools: Dict[str, Callable] = {}
        self.dynamic_tools: Dict[str, str] = {}
        self.integrations: Dict[str, MCPIntegration] = {}

    async def load_integrations(self):
        """Discover and initialize enabled integrations."""
        import yaml
        
        module_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(module_dir)
        config_path = os.path.join(backend_dir, "config", "enabled_integrations.yaml")
             
        if not os.path.exists(config_path):
            logger.warning(f"Integration config not found at {config_path}")
            return

        with open(config_path, "r") as f:
            integration_config = yaml.safe_load(f)

        if not integration_config:
            logger.info("No integrations configured")
            return

        for category, settings in integration_config.items():
            if not settings.get("enabled"):
                continue
                
            for provider_name, provider_cfg in settings.get("providers", {}).items():
                if not provider_cfg.get("enabled"):
                    continue
                
                if provider_name == "native":
                    continue

                try:
                    module_path = f"backend.src.integrations.{category}.{provider_name}"
                    module = importlib.import_module(module_path)
                    
                    class_name = "".join(x.title() for x in provider_name.split('_')) + "Integration"
                    IntegrationClass = getattr(module, class_name)
                    
                    integration = IntegrationClass(provider_cfg)
                    await integration.initialize()
                    
                    self.integrations[f"{category}.{provider_name}"] = integration
                    logger.info(f"Loaded integration: {category}.{provider_name}")
                    
                except ImportError as e:
                    logger.error(f"Failed to import integration {category}.{provider_name}: {e}")
                except AttributeError as e:
                    logger.error(f"Integration class not found for {category}.{provider_name}: {e}")
                except Exception as e:
                    logger.error(f"Failed to initialize integration {category}.{provider_name}: {e}")

    def register_system_tool(self, name: str, func: Callable, category: str = "System"):
        """Registers an immutable system tool."""
        self.system_tools[name] = {"func": func, "category": category}
        logger.debug(f"Registered system tool: {name}")

    def load_dynamic_tools(self):
        """Loads all dynamic tools from the workspace tools directory."""
        self.dynamic_tools.clear()
        for file in self.workspace.tools_path.glob("*.py"):
            tool_name = file.stem
            with open(file, "r") as f:
                code = f.read()
                
            category = "User Defined"
            first_line = code.split("\n")[0]
            if first_line.startswith("# Category:"):
                category = first_line.split(":", 1)[1].strip()
                
            self.dynamic_tools[tool_name] = {"code": code, "category": category}
        logger.info(f"Loaded {len(self.dynamic_tools)} dynamic tools")

    def create_dynamic_tool(self, name: str, code: str, category: str = "User Defined"):
        """Creates a new dynamic tool."""
        if name in self.system_tools:
            raise ValueError(f"Cannot overwrite system tool '{name}'")
        
        full_code = f"# Category: {category}\n{code}"
        
        file_path = self.workspace.get_tool_path(name)
        with open(file_path, "w") as f:
            f.write(full_code)
        
        self.dynamic_tools[name] = {"code": full_code, "category": category}
        logger.info(f"Created dynamic tool: {name}")

    def delete_dynamic_tool(self, name: str):
        """Deletes a dynamic tool."""
        if name in self.system_tools:
            raise ValueError(f"Cannot delete system tool '{name}'")
        
        if name not in self.dynamic_tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")
            
        file_path = self.workspace.get_tool_path(name)
        if file_path.exists():
            os.remove(file_path)
        
        del self.dynamic_tools[name]
        logger.info(f"Deleted dynamic tool: {name}")

    def get_tool(self, name: str) -> Optional[Callable]:
        """Retrieves a tool by name (system or dynamic)."""
        if name in self.system_tools:
            return self.system_tools[name]["func"]
        
        if name in self.dynamic_tools:
            return self._create_dynamic_tool_wrapper(name, self.dynamic_tools[name]["code"])
            
        return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists all available tools."""
        tools = []
        
        for name, info in self.system_tools.items():
            func = info["func"]
            doc = inspect.getdoc(func) or ""
            sig = str(inspect.signature(func))
            tools.append({
                "name": name,
                "description": doc,
                "type": "system",
                "category": info["category"],
                "signature": sig,
                "provider": "native"
            })
            
        for name, info in self.dynamic_tools.items():
            tools.append({
                "name": name,
                "description": "User defined tool",
                "type": "dynamic",
                "category": info["category"],
                "provider": "user_defined"
            })

        for integration_key, integration in self.integrations.items():
            for tool in integration.list_tools():
                tools.append({
                    **tool,
                    "type": "integration",
                    "provider": integration_key
                })
            
        return tools

    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Route tool call to appropriate handler with robust error handling."""
        
        # Audit log
        logger.info(f"AUDIT: call_tool('{tool_name}', {args})")
        sys.audit("mcp.registry.call_tool", tool_name, args)
        
        try:
            # Try native first
            if tool_name in self.system_tools:
                result = self.system_tools[tool_name]["func"](**args)
                logger.debug(f"System tool '{tool_name}' executed successfully")
                return result
            
            # Try integrations
            for integration in self.integrations.values():
                integration_tools = {t["name"]: t for t in integration.list_tools()}
                if tool_name in integration_tools:
                    result = await integration.call_tool(tool_name, args)
                    logger.debug(f"Integration tool '{tool_name}' executed successfully")
                    return result
            
            # Try dynamic
            if tool_name in self.dynamic_tools:
                # Dynamic tools are handled by the caller via get_tool
                logger.warning(f"Dynamic tool '{tool_name}' requires external executor")
                raise ToolExecutionError(f"Dynamic tool '{tool_name}' requires external executor")
            
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")
            
        except ToolNotFoundError:
            raise
        except ToolExecutionError:
            raise
        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_name}': {e}")
            raise ToolExecutionError(f"Execution failed: {str(e)}") from e

    def _create_dynamic_tool_wrapper(self, name: str, code: str) -> Callable:
        """Creates a callable wrapper for a dynamic tool."""
        def wrapper(*args, **kwargs):
            pass
        wrapper.__name__ = name
        return wrapper

