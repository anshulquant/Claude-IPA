#!/usr/bin/env python3
"""
LMS Workflow Example

Demonstrates how to automate tasks in your company's LMS
after authenticating with Google OAuth.

Prerequisites:
1. Run auth_helper.py first to save your login session
2. Make sure auth_state.json exists
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from browser_controller import BrowserController
from orchestrator import ClaudeOrchestrator


async def lms_workflow_example(lms_url: str, task_description: str):
    """
    Autonomous LMS workflow.
    
    Args:
        lms_url: Your LMS URL
        task_description: What you want Claude to do (e.g., "Find and open the Python course")
    """
    print("\n" + "="*70)
    print("LMS WORKFLOW")
    print("="*70)
    print(f"\nLMS URL: {lms_url}")
    print(f"Task: {task_description}\n")
    
    # Check if auth state exists
    auth_file = "auth_state.json"
    if not Path(auth_file).exists():
        print(f"[ERROR] Authentication state not found: {auth_file}")
        print("\nPlease run auth_helper.py first to save your login session:")
        print("  python workflows/auth_helper.py")
        return
    
    # Initialize
    orchestrator = ClaudeOrchestrator()
    
    # Use saved auth state to skip login
    async with BrowserController(headless=True, auth_state_file=auth_file) as browser:
        goal = task_description
        current_step = f"Starting - need to navigate to {lms_url}"
        max_steps = 15  # LMS tasks might need more steps
        step_count = 0
        
        # Loop detection
        last_actions = []
        
        print(f"Starting workflow with saved authentication...\n")
        
        # Autonomous loop
        while step_count < max_steps:
            step_count += 1
            print(f"\n{'='*70}")
            print(f"STEP {step_count}")
            print(f"{'='*70}")
            print(f"Current: {current_step}")
            
            # Capture state
            print("\n[1/4] Capturing screenshot...")
            _, _, screenshot_b64 = await browser.capture_screenshot(f"lms_step_{step_count}")
            page_text = await browser.get_page_text()
            print(f"      Screenshot captured")
            
            # Ask Claude
            print("[2/4] Asking Claude for decision...")
            decision = await orchestrator.understand_screen_and_decide(
                screenshot_b64=screenshot_b64,
                goal=goal,
                current_step=current_step,
                page_text=page_text[:1000]
            )
            
            # Display decision
            print(f"[3/4] Claude decided:")
            print(f"      Action: {decision['action']}")
            print(f"      Target: {decision['target']}")
            if decision.get('value'):
                print(f"      Value: {decision['value']}")
            print(f"      Reasoning: {decision['reasoning']}")
            print(f"      Confidence: {decision['confidence']}")
            
            # Loop detection
            action_key = f"{decision['action']}:{decision['target']}"
            last_actions.append(action_key)
            if len(last_actions) > 3 and last_actions[-1] == last_actions[-2] == last_actions[-3]:
                print(f"\n      [WARNING] Loop detected! Same action repeated 3 times.")
                print(f"      [INFO] Marking as complete to avoid infinite loop...")
                decision['action'] = 'complete'
                decision['reasoning'] = 'Loop detected, stopping workflow'
            
            # Execute
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
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"      [ERROR] Type failed: {e}")
                    
            elif decision['action'] == 'click':
                print(f"      Clicking: {decision['target']}")
                try:
                    if decision['target'].startswith('text='):
                        text = decision['target'].replace('text=', '')
                        await browser.click_by_text(text)
                    else:
                        await browser.click_element(decision['target'])
                    print(f"      [OK] Clicked successfully")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"      [ERROR] Click failed: {e}")
            
            # Update current step
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
    """Interactive menu for LMS workflows."""
    print("\n" + "="*70)
    print("LMS AUTOMATION WORKFLOW")
    print("="*70)
    
    # Get LMS URL
    lms_url = input("\nEnter your LMS URL: ").strip()
    if not lms_url:
        print("[ERROR] LMS URL is required!")
        return
    
    # Get task description
    print("\nWhat would you like Claude to do? Examples:")
    print("  - Find and open the Python programming course")
    print("  - Navigate to my assignments and show the latest one")
    print("  - Go to the dashboard and check my progress")
    
    task = input("\nTask description: ").strip()
    if not task:
        print("[ERROR] Task description is required!")
        return
    
    try:
        await lms_workflow_example(lms_url, task)
    except Exception as e:
        print(f"\n[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
