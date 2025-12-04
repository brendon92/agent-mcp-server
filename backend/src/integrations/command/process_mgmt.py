from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class ProcessMgmtIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "command"
        self.name = "process_mgmt"
        self.manager = None
        
    async def initialize(self) -> None:
        cmd = ["uvx", "kill-process-mcp"]
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Process Management integration started.")
        except Exception as e:
            print(f"Failed to start Process Management integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "kill_process",
            "description": "Kill a process by name or ID",
            "category": "command",
            "integration": "process_mgmt",
            "parameters": {
                "type": "object",
                "properties": {
                    "process": {"type": "string", "description": "Process name or PID"}
                },
                "required": ["process"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Process Management integration is not running."
            
        return await self.manager.send_request("tools/call", {
            "name": "kill-process", # Verify tool name
            "arguments": args
        })
