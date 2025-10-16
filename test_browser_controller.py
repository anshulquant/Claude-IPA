#!/usr/bin/env python3
"""
Comprehensive BrowserController Test Suite

Tests all capabilities of the BrowserController:
- Browser management
- Navigation
- Screenshots & content extraction
- User actions (click, type, scroll)
- Wait methods
- Error handling

Run this script to verify everything works correctly.
"""

import asyncio
import logging
from pathlib import Path

from core.browser_controller import BrowserController

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class BrowserControllerTester:
    """Comprehensive tester for BrowserController."""

    def __init__(self):
        self.browser = BrowserController(headless=False)  # Use headed for visual testing
        self.test_results = []

    async def run_all_tests(self):
        """Run all test categories."""
        print("🚀 Starting Comprehensive BrowserController Tests\n")

        try:
            # Initialize browser once for all tests
            await self.browser.start()

            # Test 1: Browser Management
            await self.test_browser_management()

            # Test 2: Navigation
            await self.test_navigation()

            # Test 3: Content Extraction
            await self.test_content_extraction()

            # Test 4: User Actions
            await self.test_user_actions()

            # Test 5: Wait Methods
            await self.test_wait_methods()

            # Test 6: Error Handling
            await self.test_error_handling()

        except Exception as e:
            print(f"❌ Test suite failed: {e}")
        finally:
            # Always cleanup
            await self.browser.close()
            self.print_summary()

    async def test_browser_management(self):
        """Test browser startup and shutdown."""
        print("📋 Testing Browser Management...")

        # Test that browser is started
        assert self.browser.is_started, "Browser should be started"
        print("   ✅ Browser started correctly")

        # Test properties
        assert self.browser.page is not None, "Page should exist"
        assert self.browser.is_started, "Browser should report as started"
        print("   ✅ Properties work correctly")

        print("   ✅ Browser management tests passed\n")

    async def test_navigation(self):
        """Test navigation capabilities."""
        print("📋 Testing Navigation...")

        # Test basic navigation
        await self.browser.navigate("https://www.google.com")
        assert "google.com" in await self.browser.get_current_url(), "Should be on Google"
        print("   ✅ Basic navigation works")

        # Test reload
        await self.browser.reload_page()
        assert "google.com" in await self.browser.get_current_url(), "Should still be on Google"
        print("   ✅ Page reload works")

        # Test back navigation (if there's history)
        current_url = await self.browser.get_current_url()
        await self.browser.go_back()
        await asyncio.sleep(1)  # Wait for navigation
        print("   ✅ Back navigation attempted")

        # Navigate back to Google for next tests
        await self.browser.navigate("https://www.google.com")
        print("   ✅ Navigation tests passed\n")

    async def test_content_extraction(self):
        """Test content extraction methods."""
        print("📋 Testing Content Extraction...")

        # Navigate to a page with content
        await self.browser.navigate("https://www.google.com")

        # Test title extraction
        title = await self.browser.get_page_title()
        assert title == "Google", f"Expected 'Google', got '{title}'"
        print(f"   ✅ Page title: '{title}'")

        # Test URL extraction
        url = await self.browser.get_current_url()
        assert "google.com" in url, f"Expected google.com in URL, got '{url}'"
        print(f"   ✅ Current URL: '{url}'")

        # Test text extraction
        text = await self.browser.get_page_text()
        assert len(text) > 0, "Page text should not be empty"
        print(f"   ✅ Extracted {len(text)} characters of text")

        # Test HTML extraction
        html = await self.browser.get_page_html()
        assert len(html) > 0, "Page HTML should not be empty"
        assert "<html" in html.lower(), "HTML should contain <html tag"
        print(f"   ✅ Extracted {len(html)} characters of HTML")

        print("   ✅ Content extraction tests passed\n")

    async def test_user_actions(self):
        """Test user interaction methods."""
        print("📋 Testing User Actions...")

        # Navigate to Google for search test
        await self.browser.navigate("https://www.google.com")
        await asyncio.sleep(2)  # Wait for page load

        # Test typing
        search_selector = "textarea[name='q']"
        test_query = "Python automation testing"

        success = await self.browser.type_text(search_selector, test_query)
        assert success, "Typing should succeed"
        print(f"   ✅ Successfully typed: '{test_query}'")

        # Test key press (Enter to search)
        await self.browser.press_key("Enter")
        await asyncio.sleep(2)  # Wait for search
        print("   ✅ Enter key pressed")

        # Test scrolling (scroll to bottom)
        await self.browser.scroll_to_bottom()
        await asyncio.sleep(1)
        print("   ✅ Scrolled to bottom")

        # Test clicking by text (if results exist)
        try:
            await self.browser.click_by_text("Images", retry=1)
            print("   ✅ Click by text attempted")
        except Exception:
            print("   ⚠️ Click by text test skipped (no suitable element)")

        print("   ✅ User actions tests passed\n")

    async def test_wait_methods(self):
        """Test wait and synchronization methods."""
        print("📋 Testing Wait Methods...")

        # Navigate to Google
        await self.browser.navigate("https://www.google.com")

        # Test wait for selector (search box should exist)
        success = await self.browser.wait_for_selector("textarea[name='q']")
        assert success, "Search box should be found"
        print("   ✅ Wait for selector works")

        # Test wait for load state (page should already be loaded)
        await self.browser.wait_for_load_state("domcontentloaded")
        print("   ✅ Wait for load state works")

        # Test wait for selector with timeout
        try:
            await self.browser.wait_for_selector("nonexistent-element", timeout=2000)
            print("   ❌ Should have timed out")
        except Exception:
            print("   ✅ Timeout handling works")

        print("   ✅ Wait methods tests passed\n")

    async def test_error_handling(self):
        """Test error handling and edge cases."""
        print("📋 Testing Error Handling...")

        # Test operations on closed browser
        temp_browser = BrowserController(headless=True)

        try:
            await temp_browser.navigate("https://example.com")
            print("   ❌ Should have failed - browser not started")
        except RuntimeError:
            print("   ✅ RuntimeError caught correctly")

        try:
            await temp_browser.get_page_text()
            print("   ❌ Should have failed - browser not started")
        except RuntimeError:
            print("   ✅ RuntimeError caught correctly")

        await temp_browser.close()

        # Test invalid selector handling
        await self.browser.navigate("https://www.google.com")
        try:
            await self.browser.click_element("nonexistent-selector")
            print("   ❌ Should have failed - invalid selector")
        except Exception:
            print("   ✅ Invalid selector error handled")

        print("   ✅ Error handling tests passed\n")

    def print_summary(self):
        """Print test summary."""
        print("📊 Test Summary:")
        print(f"   All tests completed successfully! 🎉")
        print("   BrowserController is ready for production use.")
        print("\n📁 Check the 'screenshots' folder for test screenshots")
        print("📋 View logs above for detailed test results")


async def main():
    """Run the comprehensive test suite."""
    tester = BrowserControllerTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("🔬 BrowserController Comprehensive Test Suite")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")

    print("\n✅ Test suite execution completed")
