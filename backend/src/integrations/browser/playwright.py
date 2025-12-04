from ..base import MCPIntegration
from typing import Dict, Any, List
import asyncio
try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

class PlaywrightIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "browser"
        self.name = "playwright"
        
    async def initialize(self) -> None:
        if async_playwright is None:
            print("Warning: playwright not installed. Playwright integration will be disabled.")
    
    async def shutdown(self) -> None:
        pass
    
    def list_tools(self) -> List[Dict[str, Any]]:
        if async_playwright is None:
            return []
            
        return [{
            "name": "playwright_fetch",
            "description": "Fetch web page content using Playwright (headless browser).",
            "category": "browser",
            "integration": "playwright",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "wait_for_selector": {"type": "string", "description": "Wait for specific element to appear"}
                },
                "required": ["url"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name != "playwright_fetch":
            raise ValueError(f"Unknown tool: {tool_name}")
            
        if async_playwright is None:
            return "Error: playwright library not installed."
            
        url = args.get("url")
        wait_for = args.get("wait_for_selector")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url)
                if wait_for:
                    await page.wait_for_selector(wait_for)
                content = await page.content()
                return content
            finally:
                await browser.close()
