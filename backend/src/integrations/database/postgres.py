from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List

class PostgresIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "database"
        self.name = "postgres"
        self.manager = None
        
    async def initialize(self) -> None:
        # Requires connection string in config or env
        db_url = self.config.get("url")
        if not db_url:
            print("Warning: Postgres URL not configured.")
            return
            
        cmd = ["npx", "-y", "@modelcontextprotocol/server-postgres", db_url]
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Postgres integration started.")
        except Exception as e:
            print(f"Failed to start Postgres integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "postgres_query",
            "description": "Execute a read-only query on PostgreSQL",
            "category": "database",
            "integration": "postgres",
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
            return "Error: Postgres integration is not running."
            
        return await self.manager.send_request("tools/call", {
            "name": "query",
            "arguments": args
        })
