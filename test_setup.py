#!/usr/bin/env python3
"""
Test script for Claude IPA MVP - Day 1 Setup Verification
Tests basic functionality without starting the full server
"""

import asyncio
import sys
import os
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported")
        
        import uvicorn
        print("✅ Uvicorn imported")
        
        import jinja2
        print("✅ Jinja2 imported")
        
        import dotenv
        print("✅ Python-dotenv imported")
        
        from api.main import app
        print("✅ FastAPI app imported")
        
        from core.workflow_executor import WorkflowExecutor
        print("✅ WorkflowExecutor imported")
        
        from core.review_queue import ReviewQueue
        print("✅ ReviewQueue imported")
        
        from workflows.data_extraction import DataExtractionWorkflow
        print("✅ DataExtractionWorkflow imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_workflow_executor():
    """Test WorkflowExecutor basic functionality"""
    print("\n🔍 Testing WorkflowExecutor...")
    
    try:
        from core.workflow_executor import WorkflowExecutor
        
        executor = WorkflowExecutor()
        print("✅ WorkflowExecutor created")
        
        # Test basic methods exist
        assert hasattr(executor, 'execute_workflow'), "execute_workflow method missing"
        assert hasattr(executor, '_execute_step'), "_execute_step method missing"
        assert hasattr(executor, '_handle_human_review'), "_handle_human_review method missing"
        
        print("✅ WorkflowExecutor methods verified")
        return True
        
    except Exception as e:
        print(f"❌ WorkflowExecutor test failed: {e}")
        return False

def test_review_queue():
    """Test ReviewQueue basic functionality"""
    print("\n🔍 Testing ReviewQueue...")
    
    try:
        from core.review_queue import ReviewQueue
        
        review_queue = ReviewQueue(confidence_threshold=0.7)
        print("✅ ReviewQueue created")
        
        # Test basic methods exist
        assert hasattr(review_queue, 'request_review'), "request_review method missing"
        assert hasattr(review_queue, '_display_review_interface'), "_display_review_interface method missing"
        assert hasattr(review_queue, 'get_review_stats'), "get_review_stats method missing"
        
        # Test stats
        stats = review_queue.get_review_stats()
        assert 'total_reviews' in stats, "Stats missing total_reviews"
        assert 'confidence_threshold' in stats, "Stats missing confidence_threshold"
        
        print("✅ ReviewQueue methods verified")
        return True
        
    except Exception as e:
        print(f"❌ ReviewQueue test failed: {e}")
        return False

def test_data_extraction():
    """Test DataExtractionWorkflow basic functionality"""
    print("\n🔍 Testing DataExtractionWorkflow...")
    
    try:
        from workflows.data_extraction import DataExtractionWorkflow
        
        workflow = DataExtractionWorkflow()
        print("✅ DataExtractionWorkflow created")
        
        # Test basic methods exist
        assert hasattr(workflow, 'execute_data_extraction'), "execute_data_extraction method missing"
        assert hasattr(workflow, 'extract_from_multiple_pages'), "extract_from_multiple_pages method missing"
        assert hasattr(workflow, 'get_extraction_templates'), "get_extraction_templates method missing"
        
        # Test templates
        templates = workflow.get_extraction_templates()
        assert len(templates) > 0, "No extraction templates found"
        
        print("✅ DataExtractionWorkflow methods verified")
        return True
        
    except Exception as e:
        print(f"❌ DataExtractionWorkflow test failed: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app configuration"""
    print("\n🔍 Testing FastAPI app...")
    
    try:
        from api.main import app
        
        # Test app exists
        assert app is not None, "FastAPI app is None"
        
        # Test routes exist
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/api/execute-workflow", "/api/workflow-status/{workflow_id}", "/api/workflow-history", "/api/health"]
        
        for expected_route in expected_routes:
            if expected_route not in routes:
                print(f"⚠️  Route {expected_route} not found in routes")
        
        print("✅ FastAPI app configuration verified")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False

def test_directory_structure():
    """Test that all required directories exist"""
    print("\n🔍 Testing directory structure...")
    
    required_dirs = [
        "core",
        "api", 
        "templates",
        "static",
        "workflows",
        "tests",
        "logs",
        "screenshots"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
        else:
            print(f"✅ Directory {dir_name} exists")
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    return True

def test_files_exist():
    """Test that all required files exist"""
    print("\n🔍 Testing required files...")
    
    required_files = [
        "requirements.txt",
        "env.example",
        ".gitignore",
        "README.md",
        "api/main.py",
        "templates/index.html",
        "static/style.css",
        "static/app.js",
        "core/workflow_executor.py",
        "core/review_queue.py",
        "workflows/data_extraction.py"
    ]
    
    missing_files = []
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
        else:
            print(f"✅ File {file_name} exists")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    return True

async def test_async_functionality():
    """Test async functionality"""
    print("\n🔍 Testing async functionality...")
    
    try:
        from core.workflow_executor import WorkflowExecutor
        
        executor = WorkflowExecutor()
        
        # Test that execute_workflow is awaitable
        import inspect
        assert inspect.iscoroutinefunction(executor.execute_workflow), "execute_workflow is not async"
        
        print("✅ Async functionality verified")
        return True
        
    except Exception as e:
        print(f"❌ Async functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Claude IPA MVP - Day 1 Setup Verification")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Directory Structure", test_directory_structure),
        ("Required Files", test_files_exist),
        ("FastAPI App", test_fastapi_app),
        ("WorkflowExecutor", test_workflow_executor),
        ("ReviewQueue", test_review_queue),
        ("DataExtractionWorkflow", test_data_extraction),
        ("Async Functionality", lambda: asyncio.run(test_async_functionality()))
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Day 1 setup is complete and ready!")
        print("\n🚀 Next steps:")
        print("1. Start the server: python api/main.py")
        print("2. Open browser: http://localhost:8000")
        print("3. Test the web UI")
        print("4. Ready for Day 2 development!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
