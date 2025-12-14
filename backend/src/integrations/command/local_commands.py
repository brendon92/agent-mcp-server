from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class LocalCommandsIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "command"
        self.name = "local_commands"
        self.manager = None
        
    async def initialize(self) -> None:
        cmd = ["npx", "-y", "mcp-server-commands"]
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Local Commands integration started.")
        except Exception as e:
            print(f"Failed to start Local Commands integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "run_command",
            "description": "Run a shell command",
            "category": "command",
            "integration": "local_commands",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                },
                "required": ["command"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Local Commands integration is not running."
            
        return await self.manager.send_request("tools/call", {
            "name": tool_name.replace("local_commands_", ""), # Assuming mapping
            "arguments": args
        })
