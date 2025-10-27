"""
Test the full workflow with real Claude to verify loop prevention works.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.workflow_executor import WorkflowExecutor
from core.browser_controller import BrowserController
from core.orchestrator import ClaudeOrchestrator


async def test_workflow():
    """Test full workflow with loop prevention"""
    print("🧪 Testing Full Workflow with Loop Prevention\n")
    print("="*60)
    
    # Create executor with real components
    executor = WorkflowExecutor(auto_approve_reviews=True)
    executor.browser_controller = BrowserController(headless=False)
    executor.orchestrator = ClaudeOrchestrator()
    
    # Set max steps to detect if loop prevention works
    executor.max_steps = 10  # Should complete in 5-7 steps
    
    try:
        # Start browser
        print("\n1️⃣ Starting browser...")
        await executor.browser_controller.start()
        print("✅ Browser started\n")
        
        # Define workflow
        goal = "Fill the form with name 'John Doe' and email 'john@example.com'"
        start_url = "https://httpbin.org/forms/post"
        
        print(f"🎯 Goal: {goal}")
        print(f"🌐 URL: {start_url}\n")
        print("="*60)
        
        # Execute workflow
        print("\n2️⃣ Executing workflow...\n")
        result = await executor.execute_workflow(goal, start_url)
        
        print("\n" + "="*60)
        print("\n📊 WORKFLOW RESULTS\n")
        print(f"Status: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
        print(f"Steps taken: {len(executor.execution_log)}")
        print(f"Max steps allowed: {executor.max_steps}")
        
        # Check if we avoided the loop
        if len(executor.execution_log) <= 10:
            print(f"\n✅ LOOP PREVENTION WORKING! (Only {len(executor.execution_log)} steps)")
        else:
            print(f"\n❌ LOOP DETECTED! ({len(executor.execution_log)} steps - should be ~5-7)")
        
        # Show execution log
        print("\n📝 Execution Log:")
        for i, log in enumerate(executor.execution_log[-10:], 1):  # Last 10 entries
            print(f"   {i}. {log.get('step', 'Unknown')}: {log.get('message', 'No message')}")
        
        # Show filled fields
        print(f"\n📝 Filled Fields: {len(executor.filled_fields)}")
        for field in executor.filled_fields:
            print(f"   - {field}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n3️⃣ Closing browser...")
        await executor.browser_controller.close()
        print("✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_workflow())
