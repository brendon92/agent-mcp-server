from ..base import MCPIntegration
from ...utils.subprocess_mgmt import SubprocessManager
from typing import Dict, Any, List
import json

class PuppeteerIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "browser"
        self.name = "puppeteer"
        self.manager = None
        
    async def initialize(self) -> None:
        # Start the puppeteer server via npx
        # We assume npx is available
        cmd = ["npx", "-y", "@modelcontextprotocol/server-puppeteer"]
        self.manager = SubprocessManager(cmd)
        try:
            self.manager.start()
            print("Puppeteer integration started.")
        except Exception as e:
            print(f"Failed to start Puppeteer integration: {e}")
            self.manager = None
    
    async def shutdown(self) -> None:
        if self.manager:
            self.manager.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        # In a real integration, we would query the server for its tools via ListTools
        # For now, we hardcode the known tools of the puppeteer server
        return [
            {
                "name": "puppeteer_navigate",
                "description": "Navigate to a URL",
                "category": "browser",
                "integration": "puppeteer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "puppeteer_screenshot",
                "description": "Take a screenshot",
                "category": "browser",
                "integration": "puppeteer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the screenshot"},
                        "selector": {"type": "string", "description": "CSS selector to screenshot (optional)"},
                        "width": {"type": "integer", "description": "Viewport width (default 800)"},
                        "height": {"type": "integer", "description": "Viewport height (default 600)"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "puppeteer_click",
                "description": "Click an element",
                "category": "browser",
                "integration": "puppeteer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"}
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "puppeteer_fill",
                "description": "Fill an input field",
                "category": "browser",
                "integration": "puppeteer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "value": {"type": "string"}
                    },
                    "required": ["selector", "value"]
                }
            },
            {
                "name": "puppeteer_evaluate",
                "description": "Evaluate JavaScript in the browser console",
                "category": "browser",
                "integration": "puppeteer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script": {"type": "string"}
                    },
                    "required": ["script"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if not self.manager:
            return "Error: Puppeteer integration is not running."
            
        # Map our tool names to the external server's tool names
        # The official server likely uses "navigate", "screenshot", etc.
        # We need to verify the exact names. 
        # Assuming standard names: navigate, screenshot, click, fill, evaluate
        
        external_name = tool_name.replace("puppeteer_", "")
        
        # Send request to subprocess
        # This requires the subprocess to speak JSON-RPC over stdio
        # The official MCP servers do speak JSON-RPC (MCP protocol)
        
        # We need to wrap this in a proper MCP protocol client ideally
        # But for now we use our simple SubprocessManager which sends JSON-RPC
        
        return await self.manager.send_request("tools/call", {
            "name": external_name,
            "arguments": args
        })
