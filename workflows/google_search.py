#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Search Workflow Demo

Goal: Automatically search Google for a query and extract results.

This demonstrates:
- Claude analyzing Google's search page
- Claude finding and filling the search box
- Claude submitting the search
- Claude extracting search results
- Claude navigating to a result (optional)

Demo Query: "Anthropic Claude AI"
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser_controller import BrowserController
from core.orchestrator import ClaudeOrchestrator


class GoogleSearchWorkflow:
    """
    Automated Google search workflow using Claude AI.
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the Google search workflow.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.browser = BrowserController(headless=headless)
        self.orchestrator = ClaudeOrchestrator()
        self.max_steps = 15
        self.search_results = []
    
    async def execute(self, search_query: str, click_first_result: bool = False) -> Dict[str, Any]:
        """
        Execute the Google search workflow.
        
        Args:
            search_query: The query to search for
            click_first_result: Whether to click the first search result
        
        Returns:
            Dictionary with execution results and extracted data
        """
        print(f"\n{'='*60}")
        print(f"🔍 GOOGLE SEARCH WORKFLOW")
        print(f"{'='*60}")
        print(f"Query: {search_query}")
        print(f"Click First Result: {click_first_result}")
        print(f"{'='*60}\n")
        
        execution_log = []
        step_count = 0
        
        # Build the goal description
        goal = f"Search Google for '{search_query}'"
        if click_first_result:
            goal += " and click on the first search result"
        
        try:
            # Start browser
            await self.browser.start()
            print("✅ Browser started\n")
            
            # Navigate to Google
            await self.browser.navigate("https://www.google.com")
            print(f"✅ Navigated to Google\n")
            await asyncio.sleep(2)  # Let page load
            
            # Main execution loop
            while step_count < self.max_steps:
                step_count += 1
                print(f"\n{'─'*60}")
                print(f"📍 STEP {step_count}")
                print(f"{'─'*60}")
                
                # Capture current state
                screenshot_path, screenshot_bytes, screenshot_b64 = await self.browser.capture_screenshot()
                page_text = await self.browser.get_page_text()
                current_url = await self.browser.get_current_url()
                page_title = await self.browser.get_page_title()
                
                print(f"📸 Screenshot saved: {screenshot_path}")
                print(f"🔗 Current URL: {current_url}")
                print(f"📄 Page Title: {page_title}")
                
                # Ask Claude what to do next
                print(f"\n🤖 Asking Claude for next action...")
                decision = await self.orchestrator.understand_screen_and_decide(
                    screenshot_b64=screenshot_b64,
                    goal=goal,
                    current_step=f"Step {step_count}: {self._get_step_context(current_url)}",
                    page_text=page_text[:2000]  # Limit text length
                )
                
                # Log the decision
                step_log = {
                    "step": step_count,
                    "url": current_url,
                    "title": page_title,
                    "decision": decision,
                    "screenshot": screenshot_path
                }
                execution_log.append(step_log)
                
                # Display Claude's decision
                print(f"\n💭 Claude's Decision:")
                print(f"   Action: {decision.get('action', 'unknown')}")
                print(f"   Target: {decision.get('target', 'N/A')}")
                print(f"   Value: {decision.get('value', 'N/A')}")
                print(f"   Reasoning: {decision.get('reasoning', 'N/A')}")
                print(f"   Confidence: {decision.get('confidence', 0):.2%}")
                
                # Check if human review is needed
                if decision.get('needs_human_review', False):
                    print(f"\n⚠️  HUMAN REVIEW REQUIRED")
                    print(f"   Confidence is below threshold")
                    approval = await self._request_human_approval(decision)
                    if not approval:
                        print("❌ Action rejected by human reviewer")
                        break
                
                # Execute the action
                action = decision.get('action', '').lower()
                
                if action == 'complete':
                    print(f"\n✅ Workflow completed successfully!")
                    print(f"   {decision.get('reasoning', 'Goal achieved')}")
                    
                    # Try to extract search results if we're on a results page
                    if 'google.com/search' in current_url:
                        await self._extract_search_results(page_text)
                    
                    break
                
                elif action == 'error':
                    print(f"\n❌ Error encountered: {decision.get('reasoning', 'Unknown error')}")
                    break
                
                elif action == 'type':
                    target = decision.get('target', '')
                    value = decision.get('value', search_query)  # Use search query if no value specified
                    
                    # Special handling: checkboxes and radio buttons should be clicked, not typed
                    if 'checkbox' in target.lower() or 'radio' in target.lower():
                        print(f"\n🖱️  Clicking {target} (checkbox/radio detected)")
                        
                        # Check if it's a CSS selector
                        is_css_selector = (
                            target.startswith('.') or 
                            target.startswith('#') or 
                            target.startswith('[') or
                            any(tag in target.lower() for tag in ['input', 'button', 'div', 'span', 'a', 'select', 'textarea'])
                        )
                        
                        if is_css_selector:
                            success = await self.browser.click_element(target)
                        else:
                            success = await self.browser.click_by_text(target)
                        
                        if success:
                            print(f"   ✅ Click successful")
                        else:
                            print(f"   ❌ Click failed")
                    else:
                        print(f"\n⌨️  Typing '{value}' into {target}")
                        success = await self.browser.type_text(target, value, clear_first=True)
                        if success:
                            print(f"   ✅ Text entered successfully")
                        else:
                            print(f"   ❌ Failed to enter text")
                
                elif action == 'click':
                    target = decision.get('target', '')
                    print(f"\n🖱️  Clicking: {target}")
                    
                    # Check if it's a CSS selector (starts with common selector patterns or contains HTML tags)
                    is_css_selector = (
                        target.startswith('.') or 
                        target.startswith('#') or 
                        target.startswith('[') or
                        any(tag in target.lower() for tag in ['input', 'button', 'div', 'span', 'a', 'select', 'textarea'])
                    )
                    
                    if is_css_selector:
                        success = await self.browser.click_element(target)
                    else:
                        success = await self.browser.click_by_text(target)
                    
                    if success:
                        print(f"   ✅ Click successful")
                        await asyncio.sleep(3)  # Wait for page response
                    else:
                        print(f"   ❌ Click failed")
                
                elif action == 'navigate':
                    url = decision.get('target', '')
                    print(f"\n🌐 Navigating to: {url}")
                    await self.browser.navigate(url)
                    await asyncio.sleep(2)
                
                elif action == 'submit':
                    print(f"\n📤 Submitting form (pressing Enter)...")
                    await self.browser.press_key("Enter")
                    await asyncio.sleep(3)  # Wait for search results
                
                elif action == 'wait':
                    duration = decision.get('value', '2')
                    print(f"\n⏳ Waiting {duration} seconds...")
                    await asyncio.sleep(float(duration))
                
                else:
                    print(f"\n⚠️  Unknown action: {action}")
                    await asyncio.sleep(1)
                
                # Small delay between steps
                await asyncio.sleep(1)
            
            # Check if we hit max steps
            if step_count >= self.max_steps:
                print(f"\n⚠️  Reached maximum steps ({self.max_steps})")
            
            # Final summary
            print(f"\n{'='*60}")
            print(f"📊 EXECUTION SUMMARY")
            print(f"{'='*60}")
            print(f"Total Steps: {step_count}")
            print(f"Actions Logged: {len(execution_log)}")
            print(f"Search Results Found: {len(self.search_results)}")
            print(f"{'='*60}\n")
            
            # Display search results if any
            if self.search_results:
                print(f"\n🔍 SEARCH RESULTS:")
                print(f"{'─'*60}")
                for i, result in enumerate(self.search_results[:5], 1):
                    print(f"{i}. {result}")
                print(f"{'─'*60}\n")
            
            return {
                "success": True,
                "steps_executed": step_count,
                "search_results": self.search_results,
                "execution_log": execution_log,
                "final_url": await self.browser.get_current_url()
            }
        
        except Exception as e:
            print(f"\n❌ Workflow failed with error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "steps_executed": step_count,
                "search_results": self.search_results,
                "execution_log": execution_log
            }
        
        finally:
            # Cleanup
            await self.browser.close()
            print("\n✅ Browser closed")
    
    def _get_step_context(self, url: str) -> str:
        """Get context description based on current URL."""
        if 'google.com/search' in url:
            return "On Google search results page"
        elif 'google.com' in url:
            return "On Google homepage"
        else:
            return "On external page"
    
    async def _extract_search_results(self, page_text: str):
        """
        Extract search results from the page text.
        
        Args:
            page_text: The text content of the page
        """
        print(f"\n📋 Extracting search results...")
        
        # Simple extraction - look for common patterns
        # In a real implementation, you'd use proper selectors
        lines = page_text.split('\n')
        for line in lines:
            line = line.strip()
            # Look for lines that might be result titles
            if len(line) > 20 and len(line) < 200 and not line.startswith('http'):
                if any(keyword in line.lower() for keyword in ['anthropic', 'claude', 'ai', 'search']):
                    if line not in self.search_results:
                        self.search_results.append(line)
        
        print(f"   Found {len(self.search_results)} potential results")
    
    async def _request_human_approval(self, decision: Dict[str, Any]) -> bool:
        """
        Request human approval for an action.
        
        Args:
            decision: The decision that needs approval
        
        Returns:
            True if approved, False if rejected
        """
        print(f"\n{'─'*60}")
        print(f"👤 HUMAN REVIEW REQUIRED")
        print(f"{'─'*60}")
        print(f"Action: {decision.get('action')}")
        print(f"Target: {decision.get('target')}")
        print(f"Value: {decision.get('value')}")
        print(f"Reasoning: {decision.get('reasoning')}")
        print(f"Confidence: {decision.get('confidence', 0):.2%}")
        print(f"{'─'*60}")
        
        # In a real system, this would integrate with the review queue
        # For demo purposes, we'll auto-approve with a warning
        print(f"⚠️  Auto-approving for demo (would normally wait for human)")
        await asyncio.sleep(2)
        return True


async def demo_simple_search():
    """
    Demo: Simple Google search without clicking results.
    """
    workflow = GoogleSearchWorkflow(headless=False)
    
    search_query = "Anthropic Claude AI"
    result = await workflow.execute(search_query, click_first_result=False)
    
    print(f"\n{'='*60}")
    print(f"🎉 DEMO COMPLETE")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Steps: {result['steps_executed']}")
    print(f"Results Found: {len(result.get('search_results', []))}")
    if 'final_url' in result:
        print(f"Final URL: {result['final_url']}")
    print(f"{'='*60}\n")


async def demo_search_and_click():
    """
    Demo: Google search and click first result.
    """
    workflow = GoogleSearchWorkflow(headless=False)
    
    search_query = "Anthropic Claude AI"
    result = await workflow.execute(search_query, click_first_result=True)
    
    print(f"\n{'='*60}")
    print(f"🎉 DEMO COMPLETE")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Steps: {result['steps_executed']}")
    print(f"Results Found: {len(result.get('search_results', []))}")
    if 'final_url' in result:
        print(f"Final URL: {result['final_url']}")
    print(f"{'='*60}\n")


async def demo_custom_search():
    """
    Demo: Custom search query from user input.
    """
    workflow = GoogleSearchWorkflow(headless=False)
    
    search_query = input("Enter search query (or press Enter for default): ").strip()
    if not search_query:
        search_query = "Anthropic Claude AI"
    
    click_result = input("Click first result? (y/n, default=n): ").strip().lower()
    click_first_result = click_result == 'y'
    
    result = await workflow.execute(search_query, click_first_result)
    
    return result


async def main():
    """
    Main entry point - run the Google search demo.
    """
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🤖 CLAUDE IPA - GOOGLE SEARCH DEMO 🤖            ║
║                                                          ║
║  This demo shows Claude automatically searching Google   ║
║  using vision and intelligent decision-making            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\nSelect demo mode:")
    print("1. Simple search (search only, no clicking)")
    print("2. Search and click first result")
    print("3. Custom search (enter your own query)")
    
    choice = input("\nEnter choice (1, 2, or 3, default=1): ").strip()
    
    if choice == "2":
        await demo_search_and_click()
    elif choice == "3":
        await demo_custom_search()
    else:
        await demo_simple_search()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
