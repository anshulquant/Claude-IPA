#!/usr/bin/env python3
"""
Test script for ClaudeOrchestrator

Tests the orchestrator with real screenshots and workflow planning.
"""

import asyncio
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from browser_controller import BrowserController
from orchestrator import ClaudeOrchestrator


async def test_understand_screen_and_decide():
    """Test screenshot analysis and decision making."""
    print("\n" + "="*60)
    print("TEST 1: Screenshot Analysis & Decision Making")
    print("="*60)
    
    orchestrator = ClaudeOrchestrator()
    
    async with BrowserController(headless=False) as browser:
        # Navigate to example.com
        print("\n1. Navigating to example.com...")
        await browser.navigate("https://example.com")
        await asyncio.sleep(2)
        
        # Capture screenshot
        print("2. Capturing screenshot...")
        _, _, screenshot_b64 = await browser.capture_screenshot("test_example")
        page_text = await browser.get_page_text()
        
        print(f"   - Screenshot captured ({len(screenshot_b64)} chars base64)")
        print(f"   - Page text extracted ({len(page_text)} chars)")
        
        # Ask Claude to analyze
        print("\n3. Asking Claude to analyze screenshot...")
        decision = await orchestrator.understand_screen_and_decide(
            screenshot_b64=screenshot_b64,
            goal="Read and understand the content on this page",
            current_step="Just landed on example.com",
            page_text=page_text
        )
        
        # Display results
        print("\n4. Claude's Decision:")
        print(f"   - Action: {decision['action']}")
        print(f"   - Target: {decision['target']}")
        print(f"   - Value: {decision.get('value', 'N/A')}")
        print(f"   - Reasoning: {decision['reasoning']}")
        print(f"   - Confidence: {decision['confidence']}")
        print(f"   - Needs Review: {decision.get('needs_human_review', False)}")
        
        # Test with a form page
        print("\n5. Testing with DuckDuckGo search page...")
        await browser.navigate("https://duckduckgo.com")
        await asyncio.sleep(2)
        
        _, _, screenshot_b64 = await browser.capture_screenshot("test_duckduckgo")
        page_text = await browser.get_page_text()
        
        decision = await orchestrator.understand_screen_and_decide(
            screenshot_b64=screenshot_b64,
            goal="Search for 'Anthropic Claude'",
            current_step="On DuckDuckGo homepage, need to find search box",
            page_text=page_text
        )
        
        print("\n6. Claude's Decision for DuckDuckGo:")
        print(f"   - Action: {decision['action']}")
        print(f"   - Target: {decision['target']}")
        print(f"   - Value: {decision.get('value', 'N/A')}")
        print(f"   - Reasoning: {decision['reasoning']}")
        print(f"   - Confidence: {decision['confidence']}")
    
    print("\n✓ Screenshot analysis test completed!")


async def test_workflow_planning():
    """Test workflow plan generation."""
    print("\n" + "="*60)
    print("TEST 2: Workflow Planning")
    print("="*60)
    
    orchestrator = ClaudeOrchestrator()
    
    # Test various goals
    test_goals = [
        "Search for Anthropic on DuckDuckGo",
        "Fill out a contact form with name and email",
        "Navigate to Wikipedia and search for Python programming"
    ]
    
    for i, goal in enumerate(test_goals, 1):
        print(f"\n{i}. Goal: {goal}")
        print("   Generating plan...")
        
        plan = await orchestrator.generate_workflow_plan(goal)
        
        print(f"   Generated {len(plan)} steps:")
        for j, step in enumerate(plan, 1):
            print(f"      {j}. {step}")
    
    print("\n✓ Workflow planning test completed!")


async def test_error_handling():
    """Test error handling."""
    print("\n" + "="*60)
    print("TEST 3: Error Handling")
    print("="*60)
    
    orchestrator = ClaudeOrchestrator()
    
    # Test with invalid base64 (should handle gracefully)
    print("\n1. Testing with invalid screenshot data...")
    decision = await orchestrator.understand_screen_and_decide(
        screenshot_b64="invalid_base64_data",
        goal="Test error handling",
        current_step="Testing",
        page_text=""
    )
    
    print(f"   - Action: {decision['action']}")
    print(f"   - Reasoning: {decision['reasoning']}")
    
    if decision['action'] == 'error':
        print("   ✓ Error handled correctly!")
    
    print("\n✓ Error handling test completed!")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ClaudeOrchestrator Test Suite")
    print("="*60)
    
    try:
        # Test 1: Screenshot analysis
        await test_understand_screen_and_decide()
        
        # Test 2: Workflow planning
        await test_workflow_planning()
        
        # Test 3: Error handling
        await test_error_handling()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
