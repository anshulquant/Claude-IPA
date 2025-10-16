#!/usr/bin/env python3
"""
Simple browser test to isolate the issue.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "core"))

from browser_controller import BrowserController


async def test_simple():
    """Test basic browser functionality."""
    print("Testing browser startup (headless mode for stability)...")
    
    browser = BrowserController(headless=True)
    
    try:
        await browser.start()
        print("[OK] Browser started successfully")
        
        await browser.navigate("https://example.com")
        print("[OK] Navigated to example.com")
        
        await asyncio.sleep(3)
        
        title = await browser.get_page_title()
        print(f"[OK] Page title: {title}")
        
    finally:
        await browser.close()
        print("[OK] Browser closed")


if __name__ == "__main__":
    asyncio.run(test_simple())
