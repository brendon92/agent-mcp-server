import asyncio
from playwright.async_api import async_playwright, Page, Browser
from ..workspace import Workspace

class BrowserTools:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None

    async def _ensure_browser(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(headless=True)
            
        if not self.page:
            self.page = await self.browser.new_page()

    async def open_page(self, url: str) -> str:
        """Opens a URL in the browser."""
        await self._ensure_browser()
        try:
            await self.page.goto(url)
            return f"Successfully opened {url}"
        except Exception as e:
            return f"Error opening page: {str(e)}"

    async def get_content(self) -> str:
        """Gets the text content of the current page."""
        if not self.page:
            return "Error: No page open."
        return await self.page.content()

    async def click(self, selector: str) -> str:
        """Clicks an element matching the selector."""
        if not self.page:
            return "Error: No page open."
        try:
            await self.page.click(selector)
            return f"Clicked {selector}"
        except Exception as e:
            return f"Error clicking {selector}: {str(e)}"

    async def type(self, selector: str, text: str) -> str:
        """Types text into an element matching the selector."""
        if not self.page:
            return "Error: No page open."
        try:
            await self.page.fill(selector, text)
            return f"Typed text into {selector}"
        except Exception as e:
            return f"Error typing into {selector}: {str(e)}"

    async def screenshot(self, filename: str) -> str:
        """Takes a screenshot and saves it to the workspace."""
        if not self.page:
            return "Error: No page open."
            
        # Validate path to ensure it's in workspace
        try:
            full_path = self.workspace.validate_path(filename)
            await self.page.screenshot(path=str(full_path))
            return f"Screenshot saved to {filename}"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"

    async def close(self):
        """Closes the browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
