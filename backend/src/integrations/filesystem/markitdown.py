from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class MarkitdownIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "filesystem"
        self.name = "markitdown"
        self.manager = None
        
    async def initialize(self) -> None:
        cmd = ["npx", "-y", "@microsoft/markitdown-mcp"] # Verify package name
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("MarkItDown integration started.")
        except Exception as e:
            print(f"Failed to start MarkItDown integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "convert_to_markdown",
            "description": "Convert file to Markdown using MarkItDown",
            "category": "filesystem",
            "integration": "markitdown",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: MarkItDown integration is not running."
            
        return await self.manager.send_request("tools/call", {
            "name": "convert", # Verify tool name
            "arguments": args
        })
