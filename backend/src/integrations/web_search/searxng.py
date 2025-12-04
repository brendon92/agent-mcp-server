from ..base import MCPIntegration
from typing import Dict, Any, List
import aiohttp

class SearxngIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "web_search"
        self.name = "searxng"
        self.instance_url = config.get("instance_url")
        
    async def initialize(self) -> None:
        if not self.instance_url:
            print("Warning: SearXNG instance URL not configured.")
    
    async def shutdown(self) -> None:
        pass
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "search_searxng",
            "description": "Search using a self-hosted SearXNG instance.",
            "category": "web_search",
            "integration": "searxng",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.instance_url:
            return "Error: SearXNG instance URL not configured."
            
        query = args.get("query")
        # Example implementation using aiohttp to query SearXNG JSON API
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.instance_url}/search", params={"q": query, "format": "json"}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("results", [])
                else:
                    return f"Error: SearXNG returned status {resp.status}"
