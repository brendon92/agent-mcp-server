from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class MultiEngineIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "web_search"
        self.name = "multi_engine"
        self.manager = None
        
    async def initialize(self) -> None:
        cmd = self.config.get("args")
        if not cmd:
            # Fallback default
            cmd = ["npx", "-y", "@aas-ee/open-websearch"]
            
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print(f"Multi-engine search integration started with command: {' '.join(cmd)}")
        except Exception as e:
            print(f"Failed to start multi-engine search integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "search_multi_engine",
            "description": "Search using multiple engines (Bing, Baidu, DuckDuckGo, Brave, Exa, CSDN). Requires npx.",
            "category": "web_search",
            "integration": "multi_engine",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "engine": {"type": "string", "description": "Specific engine to use (optional)"}
                },
                "required": ["query"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Multi-engine search integration is not running."
            
        # The open-websearch server likely exposes a tool named 'search' or similar.
        # We need to map our 'search_multi_engine' to the underlying tool.
        # Assuming the underlying tool is simply 'search' based on common MCP patterns.
        # If we could list tools from the subprocess, we would do that, but here we assume.
        
        return await self.manager.send_request("tools/call", {
            "name": "search", 
            "arguments": args
        })

