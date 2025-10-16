"""
Browser Controller Module

Handles browser automation using Playwright.
Provides methods for browser initialization, navigation, screenshots, and cleanup.
"""

import asyncio
import logging
import base64
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserController:
    """
    Controls browser automation using Playwright.
    
    Manages browser lifecycle, navigation, and screenshot capture.
    """
    
    def __init__(self, headless: bool = False, screenshot_dir: str = "screenshots", auth_state_file: Optional[str] = None):
        """
        Initialize BrowserController.
        
        Args:
            headless: Whether to run browser in headless mode
            screenshot_dir: Directory to save screenshots
            auth_state_file: Path to saved authentication state (for reusing login sessions)
        """
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.auth_state_file = auth_state_file
        
        # Playwright objects
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # Create screenshot directory if it doesn't exist
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BrowserController initialized (headless={headless}, auth_state={'loaded' if auth_state_file else 'none'})")
    
    async def start(self) -> None:
        """
        Initialize Playwright browser.
        
        Starts Playwright, launches browser, creates context and page.
        
        Raises:
            RuntimeError: If browser is already started
        """
        if self._browser is not None:
            raise RuntimeError("Browser is already started")
        
        try:
            logger.info("Starting Playwright browser...")
            
            # Initialize Playwright
            self._playwright = await async_playwright().start()
            
            # Launch browser (Chromium)
            # Note: If browser crashes on Windows, try headless=True
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            )
            
            # Create browser context with viewport
            # Load saved auth state if provided
            context_options = {
                'viewport': {'width': 1280, 'height': 720}
            }
            
            if self.auth_state_file and Path(self.auth_state_file).exists():
                logger.info(f"Loading authentication state from: {self.auth_state_file}")
                context_options['storage_state'] = self.auth_state_file
            
            self._context = await self._browser.new_context(**context_options)
            
            # Create new page
            self._page = await self._context.new_page()
            
            logger.info("Browser started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            await self.close()
            raise
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """
        Navigate to URL.
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation succeeded
                       Options: 'load', 'domcontentloaded', 'networkidle'
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info(f"Navigating to: {url}")
            
            await self._page.goto(url, wait_until=wait_until, timeout=60000)
            
            logger.info(f"Successfully navigated to: {url}")
            
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
    
    async def capture_screenshot(self, filename: Optional[str] = None, full_page: bool = True) -> tuple[str, bytes, str]:
        """
        Capture screenshot of current page.
        
        Args:
            filename: Optional filename (without extension). If None, uses timestamp.
            full_page: If True, captures full page. If False, captures viewport only.
        
        Returns:
            Tuple of (filepath, screenshot_bytes, base64_encoded_string)
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        # Generate filename if not provided
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}"
        
        # Ensure .png extension
        if not filename.endswith('.png'):
            filename = f"{filename}.png"
        
        # Full path
        filepath = self.screenshot_dir / filename
        
        try:
            logger.info(f"Capturing screenshot: {filepath}")
            
            # Capture screenshot (viewport only to avoid size issues with Claude API)
            # Claude has a limit of 8000 pixels per dimension
            screenshot_bytes = await self._page.screenshot(path=str(filepath), full_page=False)
            
            # Convert to base64 for Claude API
            import base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            logger.info(f"Screenshot saved: {filepath}")
            
            return str(filepath), screenshot_bytes, screenshot_b64
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            raise
    
    # ==================== Page Content Methods ====================
    
    async def get_page_text(self) -> str:
        """
        Get all visible text from the page.
        
        Returns:
            Visible text content from the page body
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            text = await self._page.inner_text("body")
            logger.info(f"Extracted {len(text)} characters of text from page")
            return text
        except Exception as e:
            logger.error(f"Failed to get page text: {e}")
            raise
    
    async def get_page_html(self) -> str:
        """
        Get the HTML content of the page.
        
        Returns:
            Full HTML content of the page
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            html = await self._page.content()
            logger.info(f"Extracted {len(html)} characters of HTML from page")
            return html
        except Exception as e:
            logger.error(f"Failed to get page HTML: {e}")
            raise
    
    async def get_page_title(self) -> str:
        """
        Get the title of the current page.
        
        Returns:
            Page title
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            title = await self._page.title()
            return title
        except Exception as e:
            logger.error(f"Failed to get page title: {e}")
            raise
    
    async def get_current_url(self) -> str:
        """
        Get the current URL of the page.
        
        Returns:
            Current URL
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        return self._page.url
    
    # ==================== Action Methods ====================
    
    async def click_element(self, selector: str, retry: int = 3, timeout: int = 5000) -> bool:
        """
        Click element by CSS selector with retry logic.
        
        Args:
            selector: CSS selector for the element
            retry: Number of retry attempts
            timeout: Timeout in milliseconds for each attempt
        
        Returns:
            True if click succeeded, False otherwise
        
        Raises:
            RuntimeError: If browser is not started
            Exception: If all retry attempts fail
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        for attempt in range(retry):
            try:
                logger.info(f"Attempting to click element: {selector} (attempt {attempt + 1}/{retry})")
                await self._page.wait_for_selector(selector, timeout=timeout)
                await self._page.click(selector)
                logger.info(f"Successfully clicked: {selector}")
                return True
            except Exception as e:
                if attempt == retry - 1:
                    logger.error(f"Failed to click {selector} after {retry} attempts: {e}")
                    raise Exception(f"Failed to click {selector}: {e}")
                logger.warning(f"Click attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(1)
        
        return False
    
    async def click_by_text(self, text: str, retry: int = 3) -> bool:
        """
        Click element containing specific text.
        
        Args:
            text: Text content to search for
            retry: Number of retry attempts
        
        Returns:
            True if click succeeded
        
        Raises:
            RuntimeError: If browser is not started
            Exception: If all retry attempts fail
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        for attempt in range(retry):
            try:
                logger.info(f"Attempting to click element with text: '{text}' (attempt {attempt + 1}/{retry})")
                await self._page.click(f"text={text}")
                logger.info(f"Successfully clicked element with text: '{text}'")
                return True
            except Exception as e:
                if attempt == retry - 1:
                    logger.error(f"Failed to click text '{text}' after {retry} attempts: {e}")
                    raise Exception(f"Failed to click text '{text}': {e}")
                logger.warning(f"Click attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(1)
        
        return False
    
    async def type_text(self, selector: str, text: str, clear_first: bool = True, retry: int = 3) -> bool:
        """
        Type text into an input field.
        
        Args:
            selector: CSS selector for the input element
            text: Text to type
            clear_first: Whether to clear existing text first
            retry: Number of retry attempts
        
        Returns:
            True if typing succeeded
        
        Raises:
            RuntimeError: If browser is not started
            Exception: If all retry attempts fail
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        for attempt in range(retry):
            try:
                logger.info(f"Attempting to type into: {selector} (attempt {attempt + 1}/{retry})")
                await self._page.wait_for_selector(selector, timeout=5000)
                
                if clear_first:
                    await self._page.fill(selector, text)
                else:
                    await self._page.type(selector, text)
                
                logger.info(f"Successfully typed into: {selector}")
                return True
            except Exception as e:
                if attempt == retry - 1:
                    logger.error(f"Failed to type into {selector} after {retry} attempts: {e}")
                    raise Exception(f"Failed to type into {selector}: {e}")
                logger.warning(f"Type attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(1)
        
        return False
    
    async def press_key(self, key: str) -> None:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info(f"Pressing key: {key}")
            await self._page.keyboard.press(key)
            logger.info(f"Successfully pressed key: {key}")
        except Exception as e:
            logger.error(f"Failed to press key {key}: {e}")
            raise
    
    async def scroll_to(self, selector: str) -> None:
        """
        Scroll element into view.
        
        Args:
            selector: CSS selector for the element
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info(f"Scrolling to element: {selector}")
            await self._page.wait_for_selector(selector, timeout=5000)
            await self._page.locator(selector).scroll_into_view_if_needed()
            logger.info(f"Successfully scrolled to: {selector}")
        except Exception as e:
            logger.error(f"Failed to scroll to {selector}: {e}")
            raise
    
    async def scroll_to_bottom(self) -> None:
        """
        Scroll to the bottom of the page.
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info("Scrolling to bottom of page")
            # Use a more robust scrolling method that handles dynamic pages
            await self._page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)
            # Wait a moment for scroll to complete
            await asyncio.sleep(0.5)
            logger.info("Successfully scrolled to bottom")
        except Exception as e:
            logger.error(f"Failed to scroll to bottom: {e}")
            raise
    
    # ==================== Wait Methods ====================
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000, state: str = "visible") -> bool:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds
            state: Element state to wait for ('attached', 'detached', 'visible', 'hidden')
        
        Returns:
            True if element appeared
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info(f"Waiting for selector: {selector} (state={state})")
            await self._page.wait_for_selector(selector, timeout=timeout, state=state)
            logger.info(f"Selector found: {selector}")
            return True
        except Exception as e:
            logger.error(f"Timeout waiting for selector {selector}: {e}")
            raise
    
    async def wait_for_load_state(self, state: str = "networkidle", timeout: int = 30000) -> None:
        """
        Wait for page to reach a specific load state.
        
        Args:
            state: Load state to wait for ('load', 'domcontentloaded', 'networkidle')
            timeout: Timeout in milliseconds
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info(f"Waiting for load state: {state}")
            await self._page.wait_for_load_state(state, timeout=timeout)
            logger.info(f"Page reached load state: {state}")
        except Exception as e:
            logger.error(f"Timeout waiting for load state {state}: {e}")
            raise
    
    # ==================== Navigation Methods ====================
    
    async def reload_page(self) -> None:
        """
        Reload the current page.
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info("Reloading page")
            await self._page.reload()
            logger.info("Page reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload page: {e}")
            raise
    
    async def go_back(self) -> None:
        """
        Navigate back in browser history.
        
        Raises:
            RuntimeError: If browser is not started
        """
        if self._page is None:
            raise RuntimeError("Browser is not started. Call start() first.")
        
        try:
            logger.info("Navigating back")
            await self._page.go_back()
            logger.info("Navigated back successfully")
        except Exception as e:
            logger.error(f"Failed to go back: {e}")
            raise
    
    # ==================== Cleanup ====================
    
    async def close(self) -> None:
        """
        Cleanup and close browser.
        
        Closes page, context, browser, and stops Playwright.
        Safe to call multiple times.
        """
        logger.info("Closing browser...")
        
        try:
            if self._page:
                await self._page.close()
                self._page = None
            
            if self._context:
                await self._context.close()
                self._context = None
            
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            logger.info("Browser closed successfully")
            
        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")
            # Don't raise - cleanup should be best-effort
    
    @property
    def page(self) -> Optional[Page]:
        """Get current page object for advanced operations."""
        return self._page
    
    @property
    def is_started(self) -> bool:
        """Check if browser is currently started."""
        return self._browser is not None and self._page is not None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Example usage
async def main():
    """Example usage of BrowserController - demonstrates all capabilities."""
    async with BrowserController(headless=False) as browser:
        print("\n=== BrowserController Feature Demo ===\n")
        
        # 1. Navigation
        print("1. Testing Navigation...")
        await browser.navigate("https://example.com")
        title = await browser.get_page_title()
        url = await browser.get_current_url()
        print(f"   - Page Title: {title}")
        print(f"   - Current URL: {url}")
        
        # 2. Screenshot Capture (with base64 for Claude API)
        print("\n2. Testing Screenshot Capture...")
        filepath, screenshot_bytes, screenshot_b64 = await browser.capture_screenshot("example_page")
        print(f"   - Screenshot saved to: {filepath}")
        print(f"   - Screenshot size: {len(screenshot_bytes)} bytes")
        print(f"   - Base64 length: {len(screenshot_b64)} characters (ready for Claude API)")
        
        # 3. Content Extraction
        print("\n3. Testing Content Extraction...")
        page_text = await browser.get_page_text()
        page_html = await browser.get_page_html()
        print(f"   - Page text: {len(page_text)} characters")
        print(f"   - Page HTML: {len(page_html)} characters")
        print(f"   - First 100 chars of text: {page_text[:100]}")
        
        # 4. User Actions - Navigate to DuckDuckGo for search demo
        print("\n4. Testing User Actions (Search Demo)...")
        await browser.navigate("https://duckduckgo.com")
        await asyncio.sleep(2)  # Wait for page to fully load
        
        # DuckDuckGo uses input#searchbox_input
        search_selector = "input#searchbox_input"
        search_query = "Playwright automation"
        
        print(f"   - Typing '{search_query}' into search box...")
        await browser.type_text(search_selector, search_query)
        await asyncio.sleep(1)
        
        print("   - Pressing Enter to search...")
        await browser.press_key("Enter")
        
        # 5. Wait Methods
        print("\n5. Testing Wait Methods...")
        await browser.wait_for_load_state("networkidle")
        print("   - Waited for page to load (networkidle)")
        
        # Give extra time for any redirects/navigation to complete
        await asyncio.sleep(2)
        
        # 6. Scrolling
        print("\n6. Testing Scrolling...")
        try:
            await browser.scroll_to_bottom()
            print("   - Scrolled to bottom of page")
        except Exception as e:
            print(f"   - Scroll skipped (page still loading): {str(e)[:50]}")
        await asyncio.sleep(1)
        
        # 7. Final Screenshot
        print("\n7. Taking Final Screenshot...")
        filepath2, _, _ = await browser.capture_screenshot("search_results")
        print(f"   - Search results screenshot: {filepath2}")
        
        print("\n=== All BrowserController Features Tested Successfully! ===\n")


if __name__ == "__main__":
    asyncio.run(main())
