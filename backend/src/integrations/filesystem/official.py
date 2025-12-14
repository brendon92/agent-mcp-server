from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List
import os

class OfficialIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "filesystem"
        self.name = "official"
        self.manager = None
        
    async def initialize(self) -> None:
        # Allowed directories
        allowed_dirs = self.config.get("allowed_dirs", [os.getcwd()])
        cmd = ["npx", "-y", "@modelcontextprotocol/server-filesystem"] + allowed_dirs
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Official Filesystem integration started.")
        except Exception as e:
            print(f"Failed to start Official Filesystem integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "fs_read_file",
                "description": "Read file content",
                "category": "filesystem",
                "integration": "official",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "fs_list_directory",
                "description": "List directory contents",
                "category": "filesystem",
                "integration": "official",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Official Filesystem integration is not running."
            
        external_name = tool_name.replace("fs_", "")
        if external_name == "read_file": external_name = "read_file" # mapping check
        if external_name == "list_directory": external_name = "list_directory"
        
        return await self.manager.send_request("tools/call", {
            "name": external_name,
            "arguments": args
        })
