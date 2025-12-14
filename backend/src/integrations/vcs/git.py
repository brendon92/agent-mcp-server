from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class GitIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "vcs"
        self.name = "git"
        self.manager = None
        
    async def initialize(self) -> None:
        cmd = ["npx", "-y", "@modelcontextprotocol/server-git"]
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Git integration started.")
        except Exception as e:
            print(f"Failed to start Git integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "git_read_repo",
                "description": "Read git repository info",
                "category": "vcs",
                "integration": "git",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "git_log",
                "description": "Read git log",
                "category": "vcs",
                "integration": "git",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "max_count": {"type": "integer"}
                    },
                    "required": ["path"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Git integration is not running."
        
        external_name = tool_name.replace("git_", "")
        # Mapping might be needed
        
        return await self.manager.send_request("tools/call", {
            "name": external_name,
            "arguments": args
        })
