#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form Filling Workflow Demo

Goal: Automatically fill out a web form using Claude's vision capabilities.

This demonstrates:
- Claude analyzing form fields
- Claude identifying input fields, dropdowns, and buttons
- Claude filling form data intelligently
- Claude submitting the form
- Human review for sensitive actions

Demo Form: https://httpbin.org/forms/post (simple test form)
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser_controller import BrowserController
from core.orchestrator import ClaudeOrchestrator

# Configure logging
logger = logging.getLogger(__name__)


class FormFillingWorkflow:
    """
    Automated form filling workflow using Claude AI.
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize the form filling workflow.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.browser = BrowserController(headless=headless)
        self.orchestrator = ClaudeOrchestrator()
        self.max_steps = 20
        self.form_data = {
            "custname": "John Doe",
            "custtel": "555-1234",
            "custemail": "john.doe@example.com",
            "size": "medium",
            "topping": ["bacon", "cheese"],
            "delivery": "19:00",
            "comments": "Please ring the doorbell twice."
        }
    
    async def execute(self, form_url: str, goal: str) -> Dict[str, Any]:
        """
        Execute the form filling workflow.
        
        Args:
            form_url: URL of the form to fill
            goal: Natural language description of what to do
        
        Returns:
            Dictionary with execution results
        """
        print(f"\n{'='*60}")
        print(f"🎯 FORM FILLING WORKFLOW")
        print(f"{'='*60}")
        print(f"Goal: {goal}")
        print(f"Form URL: {form_url}")
        print(f"{'='*60}\n")
        
        execution_log = []
        step_count = 0
        
        try:
            # Start browser
            await self.browser.start()
            print("✅ Browser started\n")
            
            # Navigate to form
            await self.browser.navigate(form_url)
            print(f"✅ Navigated to: {form_url}\n")
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
                logger.info(f"Extracted {len(page_text)} characters of text from page")
                
                # Get form fields
                form_fields = await self.browser.get_form_fields()
                
                # Display current state
                print(f"📸 Screenshot saved: {screenshot_path}")
                print(f"🔗 Current URL: {await self.browser.get_current_url()}")
                
                # Ask Claude what to do next
                print(f"\n🤖 Asking Claude for next action...")
                decision = await self.orchestrator.understand_screen_and_decide(
                    screenshot_b64=screenshot_b64,
                    goal=goal,
                    current_step=f"Step {step_count}: Analyzing form",
                    page_text=page_text[:2000],  # Limit text length
                    form_fields=form_fields
                )
                
                # Log the decision
                step_log = {
                    "step": step_count,
                    "url": await self.browser.get_current_url(),
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
                    break
                
                elif action == 'error':
                    print(f"\n❌ Error encountered: {decision.get('reasoning', 'Unknown error')}")
                    break
                
                elif action == 'type':
                    target = decision.get('target', '')
                    value = decision.get('value', '')
                    
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
                        success = await self.browser.type_text(target, value)
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
                        await asyncio.sleep(2)  # Wait for page response
                    else:
                        print(f"   ❌ Click failed")
                
                elif action == 'navigate':
                    url = decision.get('target', '')
                    print(f"\n🌐 Navigating to: {url}")
                    await self.browser.navigate(url)
                    await asyncio.sleep(2)
                
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
            print(f"{'='*60}\n")
            
            return {
                "success": True,
                "steps_executed": step_count,
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
                "execution_log": execution_log
            }
        
        finally:
            # Cleanup
            await self.browser.close()
            print("\n✅ Browser closed")
    
    async def execute_batch(self, form_url: str, goal: str, form_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute form filling using intelligent batch approach (RECOMMENDED).

        This method is much more efficient than execute() - it analyzes the entire form once
        and fills all fields automatically, instead of one field at a time.

        Args:
            form_url: URL of the form to fill
            goal: Natural language description of what to do
            form_data: Optional predefined data to fill the form with

        Returns:
            Dictionary with execution results
        """
        print(f"\n{'='*60}")
        print(f"🎯 BATCH FORM FILLING WORKFLOW (Intelligent Mode)")
        print(f"{'='*60}")
        print(f"Goal: {goal}")
        print(f"Form URL: {form_url}")
        print(f"{'='*60}\n")

        try:
            # Start browser
            await self.browser.start()
            print("✅ Browser started\n")

            # Navigate to form
            await self.browser.navigate(form_url)
            print(f"✅ Navigated to: {form_url}\n")
            await asyncio.sleep(2)  # Let page load

            # Capture current state
            print("📸 Analyzing form...")
            screenshot_path, screenshot_bytes, screenshot_b64 = await self.browser.capture_screenshot()
            form_fields = await self.browser.get_form_fields()

            print(f"   Screenshot: {screenshot_path}")
            print(f"   Form fields detected:\n{form_fields}\n")

            # Ask Claude to analyze and generate complete filling plan
            print("🤖 Generating intelligent filling plan...\n")
            plan = await self.orchestrator.analyze_and_fill_form(
                screenshot_b64=screenshot_b64,
                form_fields=form_fields,
                goal=goal,
                form_data=form_data or self.form_data
            )

            # Display the plan
            print(f"💭 Claude's Filling Plan:")
            print(f"   Reasoning: {plan.get('reasoning', 'N/A')}")
            print(f"   Confidence: {plan.get('confidence', 0):.2%}")
            print(f"   Total Actions: {len(plan.get('actions', []))}\n")

            # Check if human review needed
            if plan.get('needs_human_review', False):
                print(f"⚠️  HUMAN REVIEW REQUIRED")
                approval = await self._request_human_approval(plan)
                if not approval:
                    print("❌ Plan rejected by human reviewer")
                    return {
                        "success": False,
                        "error": "Rejected by human reviewer",
                        "actions_completed": 0
                    }

            # Execute all actions in the plan
            actions = plan.get('actions', [])
            if not actions:
                print("❌ No actions generated - cannot fill form")
                return {
                    "success": False,
                    "error": "No filling plan generated",
                    "actions_completed": 0
                }

            print(f"{'─'*60}")
            print(f"🚀 EXECUTING FILLING PLAN")
            print(f"{'─'*60}\n")

            actions_completed = 0
            for i, action_item in enumerate(actions, 1):
                action = action_item.get('action', '').lower()
                target = action_item.get('target', '')
                value = action_item.get('value', '')

                print(f"[{i}/{len(actions)}] {action.upper()}: {target}")
                if value:
                    print(f"        Value: {value}")

                success = False

                if action == 'type':
                    success = await self.browser.type_text(target, value)
                    if success:
                        print(f"        ✅ Typed successfully")
                    else:
                        print(f"        ❌ Failed to type")

                elif action == 'click':
                    # Special case: if target is just "button" with no attributes, try the first button
                    if target.strip().lower() == 'button':
                        # Try to click first button element
                        success = await self.browser.click_element('button')
                        if not success:
                            # Fallback: try any button by looking for common submit text
                            for text in ['Submit', 'Submit order', 'Send', 'Continue', 'Next']:
                                try:
                                    success = await self.browser.click_by_text(text)
                                    if success:
                                        break
                                except:
                                    continue
                    else:
                        # Determine if it's a CSS selector or text
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
                        print(f"        ✅ Clicked successfully")
                    else:
                        print(f"        ❌ Failed to click")

                elif action == 'select':
                    # For dropdown selection (future enhancement)
                    print(f"        ⚠️  Select action not yet implemented")
                    success = False

                else:
                    print(f"        ⚠️  Unknown action type: {action}")
                    success = False

                if success:
                    actions_completed += 1

                # Small delay between actions
                await asyncio.sleep(0.5)
                print()

            # Wait a moment to see results
            await asyncio.sleep(2)

            # Summary
            print(f"{'='*60}")
            print(f"📊 BATCH FILLING SUMMARY")
            print(f"{'='*60}")
            print(f"Actions Planned: {len(actions)}")
            print(f"Actions Completed: {actions_completed}")
            print(f"Success Rate: {actions_completed/len(actions)*100:.1f}%")
            print(f"Final URL: {await self.browser.get_current_url()}")
            print(f"{'='*60}\n")

            return {
                "success": actions_completed == len(actions),
                "actions_planned": len(actions),
                "actions_completed": actions_completed,
                "final_url": await self.browser.get_current_url()
            }

        except Exception as e:
            print(f"\n❌ Batch workflow failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "actions_completed": 0
            }

        finally:
            # Cleanup
            await self.browser.close()
            print("\n✅ Browser closed")

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


async def demo_simple_form():
    """
    Demo: Fill out a simple test form using BATCH mode (recommended).
    """
    workflow = FormFillingWorkflow(headless=False)

    # Use httpbin's test form
    form_url = "https://httpbin.org/forms/post"
    goal = "Fill out the pizza order form with customer information and submit it"

    # Use the new batch method (much more efficient!)
    result = await workflow.execute_batch(form_url, goal)

    print(f"\n{'='*60}")
    print(f"🎉 DEMO COMPLETE")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    if 'actions_completed' in result:
        print(f"Actions: {result['actions_completed']}/{result.get('actions_planned', 0)}")
    if 'final_url' in result:
        print(f"Final URL: {result['final_url']}")
    print(f"{'='*60}\n")


async def demo_simple_form_stepwise():
    """
    Demo: Fill out a simple test form using STEP-BY-STEP mode (slower, for comparison).
    """
    workflow = FormFillingWorkflow(headless=False)

    # Use httpbin's test form
    form_url = "https://httpbin.org/forms/post"
    goal = "Fill out the pizza order form with customer information and submit it"

    # Use the old step-by-step method
    result = await workflow.execute(form_url, goal)

    print(f"\n{'='*60}")
    print(f"🎉 DEMO COMPLETE")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Steps: {result['steps_executed']}")
    if 'final_url' in result:
        print(f"Final URL: {result['final_url']}")
    print(f"{'='*60}\n")


async def demo_custom_form():
    """
    Demo: Fill out a custom form with specific data.
    """
    workflow = FormFillingWorkflow(headless=False)

    # You can use any form URL here
    form_url = input("Enter form URL (or press Enter for default): ").strip()
    if not form_url:
        form_url = "https://httpbin.org/forms/post"

    goal = input("Enter your goal (or press Enter for default): ").strip()
    if not goal:
        goal = "Fill out the form with appropriate test data and submit it"

    # Use batch mode by default
    result = await workflow.execute_batch(form_url, goal)

    return result


async def main():
    """
    Main entry point - run the form filling demo.
    """
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🤖 CLAUDE IPA - FORM FILLING DEMO 🤖             ║
║                                                          ║
║  This demo shows Claude automatically filling out        ║
║  web forms using vision and intelligent decision-making  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    print("\nSelect demo mode:")
    print("1. ⚡ Batch mode - Fill entire form automatically (RECOMMENDED)")
    print("2. 🐌 Step-by-step mode - One field at a time (for comparison)")
    print("3. 📝 Custom form - Enter your own URL")

    choice = input("\nEnter choice (1, 2, or 3, default=1): ").strip()

    if choice == "2":
        await demo_simple_form_stepwise()
    elif choice == "3":
        await demo_custom_form()
    else:
        await demo_simple_form()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
