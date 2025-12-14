from ..base import MCPIntegration
from typing import Dict, Any, List
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

class DuckduckgoIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "web_search"
        self.name = "duckduckgo"
        
    async def initialize(self) -> None:
        if DDGS is None:
            print("Warning: duckduckgo-search not installed. DuckDuckGo integration will be disabled.")
        pass
    
    async def shutdown(self) -> None:
        pass
    
    def list_tools(self) -> List[Dict[str, Any]]:
        if DDGS is None:
            return []
            
        return [{
            "name": "search_duckduckgo",
            "description": "Search the web using DuckDuckGo. Returns a list of results with title, link, and snippet.",
            "category": "web_search",
            "integration": "duckduckgo",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name != "search_duckduckgo":
            raise ValueError(f"Unknown tool: {tool_name}")
            
        if DDGS is None:
            return "Error: duckduckgo-search library not installed."
            
        query = args.get("query")
        max_results = args.get("max_results", 10)
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(r)
                
        return results
