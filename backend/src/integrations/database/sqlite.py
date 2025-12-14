from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class SqliteIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "database"
        self.name = "sqlite"
        self.manager = None
        
    async def initialize(self) -> None:
        db_path = self.config.get("path", "test.db")
        cmd = ["npx", "-y", "@modelcontextprotocol/server-sqlite", "--file", db_path]
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("SQLite integration started.")
        except Exception as e:
            print(f"Failed to start SQLite integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "sqlite_query",
            "description": "Execute a query on SQLite database",
            "category": "database",
            "integration": "sqlite",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: SQLite integration is not running."
            
        return await self.manager.send_request("tools/call", {
            "name": "query",
            "arguments": args
        })
