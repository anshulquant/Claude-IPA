"""
Run multiple test scenarios to verify workflow robustness.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.workflow_executor import WorkflowExecutor
from core.browser_controller import BrowserController
from core.orchestrator import ClaudeOrchestrator


# Test scenarios (safe sites, no captcha)
TEST_SCENARIOS = [
    {
        "name": "Wikipedia Search",
        "goal": "Search for 'Python programming' on Wikipedia",
        "start_url": "https://en.wikipedia.org",
        "expected_steps": 7,
        "description": "Test search functionality"
    },
    {
        "name": "Example.com Text",
        "goal": "Read the main heading text from example.com",
        "start_url": "https://example.com",
        "expected_steps": 4,
        "description": "Test simple text extraction"
    },
    {
        "name": "MDN Search",
        "goal": "Search for 'JavaScript arrays' on MDN",
        "start_url": "https://developer.mozilla.org",
        "expected_steps": 7,
        "description": "Test documentation search"
    },
    {
        "name": "W3Schools Navigation",
        "goal": "Navigate to W3Schools HTML try-it editor",
        "start_url": "https://www.w3schools.com/html/tryit.asp?filename=tryhtml_default",
        "expected_steps": 3,
        "description": "Test simple navigation"
    }
]


async def run_scenario(scenario, scenario_num, total_scenarios):
    """Run a single test scenario"""
    print("\n" + "="*70)
    print(f"🧪 TEST {scenario_num}/{total_scenarios}: {scenario['name']}")
    print("="*70)
    print(f"📝 Description: {scenario['description']}")
    print(f"🎯 Goal: {scenario['goal']}")
    print(f"🌐 URL: {scenario['start_url']}")
    print(f"📊 Expected Steps: ~{scenario['expected_steps']}")
    print("-"*70)
    
    # Create executor
    executor = WorkflowExecutor(auto_approve_reviews=True)
    executor.browser_controller = BrowserController(headless=True)  # Headless for speed
    executor.orchestrator = ClaudeOrchestrator()
    executor.max_steps = 15  # Reasonable limit
    
    start_time = datetime.now()
    result = {
        "name": scenario['name'],
        "success": False,
        "steps": 0,
        "time": 0,
        "error": None
    }
    
    try:
        # Start browser
        print("\n1️⃣ Starting browser...")
        await executor.browser_controller.start()
        print("✅ Browser started")
        
        # Execute workflow
        print(f"\n2️⃣ Executing workflow...")
        workflow_result = await executor.execute_workflow(
            scenario['goal'],
            scenario['start_url']
        )
        
        # Calculate metrics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # WorkflowResult is an object, not a dict - access attributes directly
        result['success'] = workflow_result.success if hasattr(workflow_result, 'success') else False
        result['steps'] = len(executor.execution_log)
        result['time'] = duration
        
        # Print results
        print("\n" + "-"*70)
        print("📊 RESULTS:")
        print(f"   Status: {'✅ PASS' if result['success'] else '❌ FAIL'}")
        print(f"   Steps: {result['steps']} (expected ~{scenario['expected_steps']})")
        print(f"   Time: {duration:.1f}s")
        print(f"   Filled Fields: {len(executor.filled_fields)}")
        
        # Check if within expected range
        if result['steps'] <= scenario['expected_steps'] + 5:
            print(f"   ✅ Step count reasonable")
        else:
            print(f"   ⚠️ More steps than expected")
        
        # Show last few log entries
        print("\n📝 Last Actions:")
        for log in executor.execution_log[-5:]:
            print(f"   - {log.get('step', 'Unknown')}: {log.get('message', 'No message')[:60]}")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n3️⃣ Closing browser...")
        try:
            await executor.browser_controller.close()
            print("✅ Browser closed")
        except:
            pass
    
    return result


async def run_all_scenarios():
    """Run all test scenarios"""
    print("\n" + "="*70)
    print("🚀 RUNNING TEST SCENARIOS")
    print("="*70)
    print(f"Total scenarios: {len(TEST_SCENARIOS)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        result = await run_scenario(scenario, i, len(TEST_SCENARIOS))
        results.append(result)
        
        # Wait between tests
        if i < len(TEST_SCENARIOS):
            print("\n⏳ Waiting 3 seconds before next test...")
            await asyncio.sleep(3)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    print("\n" + "-"*70)
    print("Detailed Results:")
    print("-"*70)
    
    for r in results:
        status = "✅ PASS" if r['success'] else "❌ FAIL"
        error_msg = f" ({r['error'][:40]}...)" if r['error'] else ""
        print(f"{status} | {r['name']:<25} | {r['steps']:2} steps | {r['time']:5.1f}s{error_msg}")
    
    print("\n" + "="*70)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return results


if __name__ == "__main__":
    print("\n🧪 Test Scenario Runner")
    print("Testing workflow with safe, automation-friendly sites\n")
    
    # Run all scenarios
    asyncio.run(run_all_scenarios())
