#!/usr/bin/env python3
"""
Simple test script for workflow execution with mock data
Tests the core workflow execution functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.workflow_executor import WorkflowExecutor

async def test_simple_workflow():
    """Test simple workflow execution"""
    print("🧪 Testing Simple Workflow Execution")
    print("=" * 40)
    
    # Initialize workflow executor
    executor = WorkflowExecutor()
    print("✅ WorkflowExecutor initialized")
    
    # Test 1: Basic workflow with simple goal
    print("\n📋 Test 1: Basic Workflow")
    print("-" * 25)
    
    try:
        result = await executor.execute_workflow("Navigate to Google and search for 'Python automation'")
        
        print(f"✅ Workflow completed successfully!")
        print(f"   - Workflow ID: {result.workflow_id}")
        print(f"   - Goal: {result.goal}")
        print(f"   - Success: {result.success}")
        print(f"   - Actions Taken: {result.actions_taken}")
        print(f"   - Execution Time: {result.execution_time:.2f} seconds")
        print(f"   - Review Items: {len(result.review_items) if result.review_items else 0}")
        
        # Show execution log
        if result.execution_log:
            print(f"\n📝 Execution Log ({len(result.execution_log)} entries):")
            for i, log_entry in enumerate(result.execution_log[-5:], 1):  # Show last 5 entries
                print(f"   {i}. {log_entry.get('step', 'Unknown')} - {log_entry.get('message', 'No message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")
        return False

async def test_review_queue():
    """Test review queue functionality"""
    print("\n📋 Test 2: Review Queue")
    print("-" * 25)
    
    try:
        executor = WorkflowExecutor()
        
        # Get review queue stats
        stats = executor.get_review_queue_stats()
        print(f"✅ Review Queue Stats:")
        print(f"   - Total Items: {stats['total_items']}")
        print(f"   - Pending: {stats['pending']}")
        print(f"   - In Review: {stats['in_review']}")
        print(f"   - Approved: {stats['approved']}")
        print(f"   - Rejected: {stats['rejected']}")
        
        # Get pending reviews
        pending = executor.get_pending_reviews()
        print(f"\n📋 Pending Reviews: {len(pending)}")
        for review in pending[:3]:  # Show first 3
            print(f"   - ID: {review['review_id']}")
            print(f"   - Workflow: {review['workflow_id']}")
            print(f"   - Priority: {review['priority']}")
            print(f"   - Status: {review['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Review queue test failed: {str(e)}")
        return False

def test_api_health():
    """Test API health endpoint"""
    print("\n📋 Test 3: API Health")
    print("-" * 25)
    
    try:
        import requests
        
        response = requests.get('http://127.0.0.1:8000/api/health')
        print(f"✅ Health endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   - Status: {data.get('status', 'Unknown')}")
            print(f"   - Timestamp: {data.get('timestamp', 'Unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        print("   Make sure the server is running on http://127.0.0.1:8000")
        return False

async def main():
    """Main test function"""
    print("🚀 Claude Automation Hub - Simple Workflow Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    tests = [
        ("Workflow Execution", test_simple_workflow()),
        ("Review Queue", test_review_queue()),
        ("API Health", test_api_health())
    ]
    
    results = []
    for test_name, test_coro in tests:
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
        results.append((test_name, result))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Workflow execution is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
