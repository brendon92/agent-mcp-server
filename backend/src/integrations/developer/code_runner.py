from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class CodeRunnerIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "developer"
        self.name = "code_runner"
        self.manager = None
        
    async def initialize(self) -> None:
        cmd = ["npx", "-y", "mcp-code-runner"] # Verify package
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Code Runner integration started.")
        except Exception as e:
            print(f"Failed to start Code Runner integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "run_code",
            "description": "Run code in a docker container",
            "category": "developer",
            "integration": "code_runner",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {"type": "string"},
                    "code": {"type": "string"}
                },
                "required": ["language", "code"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Code Runner integration is not running."
            
        return await self.manager.send_request("tools/call", {
            "name": "run", # Verify tool name
            "arguments": args
        })
