#!/usr/bin/env python3
"""
Simple Search Workflow Demo

Goal: Search DuckDuckGo for "Anthropic Claude" and read the first result.

This demonstrates:
- Claude analyzing search page
- Claude finding and filling search box
- Claude submitting search
- Claude finding and clicking first result
- Claude reading the result page
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from browser_controller import BrowserController
from orchestrator import ClaudeOrchestrator


async def simple_search_workflow():
    """
    Autonomous search workflow.
    
    Claude will:
    1. Navigate to DuckDuckGo
    2. Find the search box
    3. Type "Anthropic Claude"
    4. Submit the search
    5. Click the first result
    6. Read the content
    """
    print("\n" + "="*70)
    print("SIMPLE SEARCH WORKFLOW")
    print("="*70)
    print("\nGoal: Search DuckDuckGo for 'Anthropic Claude' and read first result")
    print("Claude will autonomously decide each step!\n")
    
    # Initialize
    orchestrator = ClaudeOrchestrator()
    
    # Using headless=True for stability (non-headless crashes on some Windows systems)
    async with BrowserController(headless=True) as browser:
        # Define goal
        goal = "Search DuckDuckGo for 'Anthropic Claude' and click the first result"
        current_step = "Starting - need to navigate to DuckDuckGo"
        max_steps = 10  # Safety limit
        step_count = 0
        
        # Loop detection
        last_actions = []
        
        print(f"Starting workflow...\n")
        
        # Autonomous loop - Claude decides everything!
        while step_count < max_steps:
            step_count += 1
            print(f"\n{'='*70}")
            print(f"STEP {step_count}")
            print(f"{'='*70}")
            print(f"Current: {current_step}")
            
            # 1. Capture current state
            print("\n[1/4] Capturing screenshot...")
            _, _, screenshot_b64 = await browser.capture_screenshot(f"search_step_{step_count}")
            page_text = await browser.get_page_text()
            print(f"      Screenshot captured")
            
            # 2. Ask Claude: "What should I do next?"
            print("[2/4] Asking Claude for decision...")
            decision = await orchestrator.understand_screen_and_decide(
                screenshot_b64=screenshot_b64,
                goal=goal,
                current_step=current_step,
                page_text=page_text[:1000]  # Limit text
            )
            
            # 3. Display Claude's decision
            print(f"[3/4] Claude decided:")
            print(f"      Action: {decision['action']}")
            print(f"      Target: {decision['target']}")
            if decision.get('value'):
                print(f"      Value: {decision['value']}")
            print(f"      Reasoning: {decision['reasoning']}")
            print(f"      Confidence: {decision['confidence']}")
            
            # Detect loops - if same action repeated 3 times, force type action
            action_key = f"{decision['action']}:{decision['target']}"
            last_actions.append(action_key)
            if len(last_actions) > 3 and last_actions[-1] == last_actions[-2] == last_actions[-3]:
                print(f"\n      [WARNING] Loop detected! Same action repeated 3 times.")
                print(f"      [FIX] Forcing 'type' action instead...")
                decision['action'] = 'type'
                decision['value'] = 'Anthropic Claude'
                decision['reasoning'] = 'Loop detected, forcing type action'
            
            # 4. Execute Claude's decision
            print(f"[4/4] Executing action...")
            
            if decision['action'] == 'complete':
                print(f"\n{'='*70}")
                print(f"SUCCESS! Goal achieved in {step_count} steps!")
                print(f"{'='*70}")
                print(f"\nFinal state: {decision['reasoning']}")
                break
                
            elif decision['action'] == 'error':
                print(f"\n{'='*70}")
                print(f"ERROR: {decision['reasoning']}")
                print(f"{'='*70}")
                break
                
            elif decision['action'] == 'navigate':
                print(f"      Navigating to: {decision['target']}")
                try:
                    await browser.navigate(decision['target'])
                    print(f"      [OK] Navigation successful")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"      [ERROR] Navigation failed: {e}")
                    
            elif decision['action'] == 'type':
                print(f"      Typing '{decision['value']}' into '{decision['target']}'")
                try:
                    await browser.type_text(decision['target'], decision['value'])
                    print(f"      [OK] Typed successfully")
                    
                    # If typing into a search box, press Enter to submit
                    if 'search' in decision['target'].lower() or 'q' in decision['target'].lower():
                        print(f"      [AUTO] Pressing Enter to submit search...")
                        await browser.press_key('Enter')
                        print(f"      [OK] Pressed Enter")
                        await asyncio.sleep(3)  # Wait for results to load
                    else:
                        await asyncio.sleep(1)
                except Exception as e:
                    print(f"      [ERROR] Type failed: {e}")
                    
            elif decision['action'] == 'click':
                print(f"      Clicking: {decision['target']}")
                try:
                    # Try clicking by text first
                    if decision['target'].startswith('text='):
                        text = decision['target'].replace('text=', '')
                        await browser.click_by_text(text)
                    else:
                        await browser.click_element(decision['target'])
                    print(f"      [OK] Clicked successfully")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"      [ERROR] Click failed: {e}")
            
            # Update current step for next iteration
            current_step = decision['reasoning']
        
        if step_count >= max_steps:
            print(f"\n{'='*70}")
            print(f"Reached maximum steps ({max_steps})")
            print(f"{'='*70}")
        
        # Show final page info
        print(f"\n{'='*70}")
        print(f"FINAL PAGE INFO")
        print(f"{'='*70}")
        final_url = await browser.get_current_url()
        final_title = await browser.get_page_title()
        print(f"URL: {final_url}")
        print(f"Title: {final_title}")
        
        print(f"\n{'='*70}")
        print(f"WORKFLOW COMPLETED")
        print(f"{'='*70}")


async def main():
    """Run the simple search workflow."""
    try:
        await simple_search_workflow()
    except Exception as e:
        print(f"\n[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
