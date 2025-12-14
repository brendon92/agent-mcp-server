from ..base import MCPIntegration
from typing import Dict, Any, List
from playwright.async_api import async_playwright

class FetchIntegration(MCPIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.category = "browser"
        self.name = "fetch"
        self.browser = None
        self.playwright = None
        
    async def initialize(self) -> None:
        try:
            print("Fetch integration initialized (using playwright).")
        except Exception as e:
            print(f"Failed to initialize Fetch integration: {e}")
    
    async def shutdown(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "fetch_url",
            "description": "Fetch content from a URL and return as text",
            "category": "browser",
            "integration": "fetch",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            }
        }]
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name == "fetch_url":
            url = args.get("url")
            if not url:
                return {"error": "URL parameter is required"}
            
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, timeout=30000)
                    content = await page.content()
                    text = await page.evaluate("() => document.body.innerText")
                    await browser.close()
                    
                    return {
                        "url": url,
                        "text": text,
                        "html_length": len(content)
                    }
            except Exception as e:
                return {"error": f"Failed to fetch URL: {str(e)}"}
            
        raise ValueError(f"Unknown tool: {tool_name}")
