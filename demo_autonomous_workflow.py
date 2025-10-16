#!/usr/bin/env python3
"""
REAL-WORLD DEMO: Autonomous Web Automation with Claude

This demonstrates the complete use case:
- Claude analyzes screenshots
- Claude decides what to do next
- Browser executes the actions
- Loop continues until goal is achieved

This is the "magic" - fully autonomous web browsing!
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "core"))

from browser_controller import BrowserController
from orchestrator import ClaudeOrchestrator


async def autonomous_workflow_demo():
    """
    Demonstrate fully autonomous web automation.
    
    Goal: Navigate to example.com and read the content
    Claude will decide each step autonomously!
    """
    print("\n" + "="*70)
    print("🤖 AUTONOMOUS WEB AUTOMATION DEMO")
    print("="*70)
    print("\nGoal: Navigate to example.com and understand the content")
    print("Claude will autonomously decide each action!\n")
    
    # Initialize
    orchestrator = ClaudeOrchestrator()
    
    # Note: Using headless=True for stability on Windows
    # If you want to see the browser, try headless=False (may crash on some systems)
    async with BrowserController(headless=True) as browser:
        # Define goal
        goal = "Navigate to example.com and read the main content"
        current_step = "Starting automation"
        max_steps = 5  # Safety limit
        step_count = 0
        
        # Navigate to starting point
        print(f"Step {step_count}: Navigating to example.com...")
        await browser.navigate("https://example.com")
        await asyncio.sleep(2)
        
        # Autonomous loop - Claude decides everything!
        while step_count < max_steps:
            step_count += 1
            print(f"\n{'='*70}")
            print(f"🔄 STEP {step_count}: {current_step}")
            print(f"{'='*70}")
            
            # 1. Capture current state
            print("📸 Capturing screenshot...")
            _, _, screenshot_b64 = await browser.capture_screenshot(f"step_{step_count}")
            page_text = await browser.get_page_text()
            print(f"   ✓ Screenshot captured")
            print(f"   ✓ Page text extracted ({len(page_text)} chars)")
            
            # 2. Ask Claude: "What should I do next?"
            print("\n🧠 Asking Claude: 'What should I do next?'")
            decision = await orchestrator.understand_screen_and_decide(
                screenshot_b64=screenshot_b64,
                goal=goal,
                current_step=current_step,
                page_text=page_text[:500]  # Limit text to avoid huge screenshots
            )
            
            # 3. Display Claude's decision
            print(f"\n💡 Claude's Decision:")
            print(f"   Action: {decision['action']}")
            print(f"   Target: {decision['target']}")
            if decision.get('value'):
                print(f"   Value: {decision['value']}")
            print(f"   Reasoning: {decision['reasoning']}")
            print(f"   Confidence: {decision['confidence']}")
            
            # 4. Execute Claude's decision
            if decision['action'] == 'complete':
                print(f"\n✅ SUCCESS! Goal achieved!")
                print(f"   {decision['reasoning']}")
                break
                
            elif decision['action'] == 'error':
                print(f"\n❌ ERROR: {decision['reasoning']}")
                break
                
            elif decision['action'] == 'click':
                print(f"\n👆 Executing: Click on '{decision['target']}'")
                try:
                    # Try clicking by text first
                    if decision['target'].startswith('text='):
                        text = decision['target'].replace('text=', '')
                        await browser.click_by_text(text)
                    else:
                        await browser.click_element(decision['target'])
                    print(f"   ✓ Clicked successfully")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"   ✗ Click failed: {e}")
                    
            elif decision['action'] == 'type':
                print(f"\n⌨️  Executing: Type '{decision['value']}' into '{decision['target']}'")
                try:
                    await browser.type_text(decision['target'], decision['value'])
                    print(f"   ✓ Typed successfully")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"   ✗ Type failed: {e}")
                    
            elif decision['action'] == 'navigate':
                print(f"\n🌐 Executing: Navigate to '{decision['target']}'")
                try:
                    await browser.navigate(decision['target'])
                    print(f"   ✓ Navigated successfully")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"   ✗ Navigation failed: {e}")
            
            # Update current step for next iteration
            current_step = decision['reasoning']
        
        if step_count >= max_steps:
            print(f"\n⚠️  Reached maximum steps ({max_steps})")
        
        print(f"\n{'='*70}")
        print("🎬 DEMO COMPLETED")
        print(f"{'='*70}")


async def workflow_planning_demo():
    """
    Demonstrate workflow planning from natural language.
    """
    print("\n" + "="*70)
    print("📋 WORKFLOW PLANNING DEMO")
    print("="*70)
    
    orchestrator = ClaudeOrchestrator()
    
    # Example: User gives natural language goal
    user_goal = "Search for 'Claude AI' on DuckDuckGo and click the first result"
    
    print(f"\n👤 User Goal: {user_goal}")
    print("\n🧠 Claude is breaking this down into steps...")
    
    # Claude generates step-by-step plan
    plan = await orchestrator.generate_workflow_plan(user_goal)
    
    print(f"\n📝 Generated Workflow Plan ({len(plan)} steps):")
    for i, step in enumerate(plan, 1):
        print(f"   {i}. {step}")
    
    print(f"\n💡 This plan can now be executed step-by-step!")
    print("   Each step would use understand_screen_and_decide() to execute it.")


async def comparison_demo():
    """
    Show the difference between traditional automation vs AI-guided.
    """
    print("\n" + "="*70)
    print("🔄 TRADITIONAL vs AI-GUIDED AUTOMATION")
    print("="*70)
    
    print("\n❌ TRADITIONAL AUTOMATION (Brittle):")
    print("   1. Hard-coded selectors: click('#search-button')")
    print("   2. Breaks when website changes")
    print("   3. Cannot adapt to unexpected situations")
    print("   4. Requires manual updates for each change")
    
    print("\n✅ AI-GUIDED AUTOMATION (Adaptive):")
    print("   1. Claude sees the page visually")
    print("   2. Understands context and intent")
    print("   3. Adapts to layout changes")
    print("   4. Makes intelligent decisions")
    print("   5. Can handle unexpected popups/modals")
    
    print("\n💡 Example:")
    print("   Traditional: 'Click button with ID submit-btn'")
    print("              → Breaks if ID changes")
    print("\n   AI-Guided: 'Find and click the submit button'")
    print("             → Claude finds it visually, even if ID changes!")


async def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("🎯 CLAUDE IPA - COMPLETE USE CASE DEMONSTRATION")
    print("="*70)
    
    # Demo 1: Show the concept
    await comparison_demo()
    
    input("\n\nPress Enter to see Workflow Planning demo...")
    
    # Demo 2: Workflow planning
    await workflow_planning_demo()
    
    input("\n\nPress Enter to see LIVE Autonomous Automation...")
    
    # Demo 3: Live autonomous automation
    await autonomous_workflow_demo()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED!")
    print("="*70)
    print("\n🎯 What you just saw:")
    print("   1. Claude breaks down goals into steps (workflow planning)")
    print("   2. Claude analyzes screenshots visually")
    print("   3. Claude decides actions autonomously")
    print("   4. Browser executes Claude's decisions")
    print("   5. Loop continues until goal achieved")
    print("\n💡 This is the foundation for:")
    print("   - Form filling automation")
    print("   - Data extraction from websites")
    print("   - E2E testing without brittle selectors")
    print("   - Any web task described in natural language!")
    print("\n🚀 Next: Build complete workflows and web UI!")


if __name__ == "__main__":
    asyncio.run(main())
