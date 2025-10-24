#!/usr/bin/env python3
"""
Comprehensive Test Suite for Claude Automation Hub
Tests all enhanced components and features
"""

import asyncio
import json
import os
import sys
import time
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.workflow_executor import WorkflowExecutor, ExecutionStatus, ErrorType, RetryConfig
from core.review_queue import ReviewQueue, ReviewItem, ReviewStatus, ReviewPriority, ReviewCategory
from utils.log_utils import setup_advanced_logging, performance_logger, MemoryMonitor
from config.logging_config import setup_logging

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def add_result(self, test_name, passed, error=None):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        self.test_results.append({
            'test': test_name,
            'status': status,
            'error': str(error) if error else None
        })
        
        print(f"{status} - {test_name}")
        if error:
            print(f"    Error: {error}")

def test_workflow_executor_error_handling():
    """Test enhanced error handling and recovery system"""
    print("\n🧪 Testing WorkflowExecutor Error Handling")
    print("=" * 50)
    
    results = TestResults()
    
    try:
        # Test 1: Circuit Breaker Functionality
        executor = WorkflowExecutor()
        
        # Simulate multiple failures to trigger circuit breaker
        for i in range(5):
            executor.circuit_breaker_failures += 1
        
        circuit_open = executor._is_circuit_breaker_open()
        results.add_result("Circuit Breaker Opens After Threshold", circuit_open)
        
        # Reset circuit breaker
        executor.circuit_breaker_failures = 0
        executor.last_failure_time = None
        
        circuit_closed = not executor._is_circuit_breaker_open()
        results.add_result("Circuit Breaker Resets", circuit_closed)
        
        # Test 2: Error Classification
        test_errors = [
            (Exception("Network timeout"), ErrorType.NETWORK_ERROR),
            (Exception("Connection refused"), ErrorType.NETWORK_ERROR),
            (Exception("Invalid credentials"), ErrorType.PERMISSION_ERROR),
            (Exception("Permission denied"), ErrorType.PERMISSION_ERROR),
            (Exception("File not found"), ErrorType.VALIDATION_ERROR),
            (Exception("Unknown error"), ErrorType.UNKNOWN_ERROR)
        ]
        
        for error, expected_type in test_errors:
            error_type = executor._classify_error(error)
            results.add_result(f"Error Classification: {type(error).__name__}", 
                             error_type == expected_type)
        
        # Test 3: Retry Configuration
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0
        )
        
        results.add_result("Retry Configuration Creation", retry_config.max_retries == 3)
        
        # Test 4: Retry Delay Calculation
        delay1 = executor._calculate_retry_delay(1, retry_config)
        delay2 = executor._calculate_retry_delay(2, retry_config)
        
        results.add_result("Retry Delay Increases", delay2 > delay1)
        results.add_result("Retry Delay Within Bounds", 0 < delay1 < retry_config.max_delay)
        
        # Test 5: Performance Metrics
        executor._update_performance_metrics(1.5, True, 0)
        metrics = executor.get_performance_metrics()
        
        results.add_result("Performance Metrics Tracking", 
                         metrics['total_execution_time'] > 0)
        results.add_result("Success Rate Calculation", 
                         metrics['success_rate'] == 100.0)
        
    except Exception as e:
        results.add_result("WorkflowExecutor Error Handling", False, e)
    
    return results

def test_review_queue_enhancements():
    """Test enhanced review queue features"""
    print("\n🧪 Testing Review Queue Enhancements")
    print("=" * 50)
    
    results = TestResults()
    
    try:
        # Test 1: Review Queue Initialization
        queue = ReviewQueue()
        results.add_result("Review Queue Initialization", queue is not None)
        
        # Test 2: Adding Review Items with Enhanced Features
        review_item = queue.add_review_item(
            workflow_id="test_workflow_001",
            step_number=1,
            action_type="click",
            action_data={"element": "button"},
            reason="Test review item",
            category=ReviewCategory.SECURITY,
            tags=["test", "security"]
        )
        
        results.add_result("Enhanced Review Item Creation", review_item is not None)
        results.add_result("Review Item Has Category", review_item.category == ReviewCategory.SECURITY)
        results.add_result("Review Item Has Tags", len(review_item.tags) > 0)
        results.add_result("Review Item Has Estimated Time", review_item.estimated_review_time > 0)
        
        # Test 3: Priority Assignment
        high_priority_item = queue.add_review_item(
            workflow_id="test_workflow_002",
            step_number=2,
            action_type="type",
            action_data={"text": "password"},
            reason="High confidence security issue",
            priority=ReviewPriority.HIGH,
            category=ReviewCategory.SECURITY
        )
        
        results.add_result("High Priority Assignment", 
                         high_priority_item.priority == ReviewPriority.HIGH)
        
        # Test 4: Filtering Reviews
        security_reviews = queue.filter_reviews(category=ReviewCategory.SECURITY)
        results.add_result("Category Filtering", len(security_reviews) >= 2)
        
        high_priority_reviews = queue.filter_reviews(priority=ReviewPriority.HIGH)
        results.add_result("Priority Filtering", len(high_priority_reviews) >= 1)
        
        # Test 5: Search Functionality
        search_results = queue.search_reviews("security")
        results.add_result("Search Functionality", len(search_results) >= 1)
        
        # Test 6: Batch Operations
        review_ids = [review_item.id, high_priority_item.id]
        batch_result = queue.batch_approve(review_ids, "test_reviewer", "Batch approval test")
        
        results.add_result("Batch Approval", len(batch_result) == 2)
        
        # Test 7: Review History
        history = queue.get_review_history(review_item.id)
        results.add_result("Review History Tracking", len(history) > 0)
        
        # Test 8: Export Functionality
        export_file = queue.export_review_data("test_export.json")
        results.add_result("Export Functionality", os.path.exists("test_export.json"))
        
        # Cleanup
        if os.path.exists("test_export.json"):
            os.remove("test_export.json")
        
    except Exception as e:
        results.add_result("Review Queue Enhancements", False, e)
    
    return results

def test_logging_system():
    """Test advanced logging and monitoring system"""
    print("\n🧪 Testing Advanced Logging System")
    print("=" * 50)
    
    results = TestResults()
    
    try:
        # Test 1: Logging Configuration
        logging_config = setup_advanced_logging("test")
        results.add_result("Logging Configuration Setup", logging_config is not None)
        
        # Test 2: Performance Logger Decorator
        @performance_logger("test_operation")
        def test_function():
            time.sleep(0.1)
            return "success"
        
        result = test_function()
        results.add_result("Performance Logger Decorator", result == "success")
        
        # Test 3: Memory Monitor
        memory_monitor = MemoryMonitor()
        memory_usage = memory_monitor.get_memory_usage()
        
        results.add_result("Memory Monitor Initialization", memory_monitor is not None)
        results.add_result("Memory Usage Tracking", memory_usage > 0)
        
        # Test 4: Log Sanitization
        from utils.log_utils import sanitize_log_data
        
        sensitive_data = {
            "password": "secret123",
            "api_key": "sk-1234567890",
            "normal_field": "safe_value"
        }
        
        sanitized = sanitize_log_data(sensitive_data)
        results.add_result("Password Sanitization", "password[REDACTED]" in str(sanitized))
        results.add_result("API Key Sanitization", "api_key[REDACTED]" in str(sanitized))
        results.add_result("Normal Field Preserved", sanitized.get("normal_field") == "safe_value")
        
        # Test 5: Log File Creation
        log_dir = Path("logs")
        log_files = list(log_dir.glob("*.log")) if log_dir.exists() else []
        results.add_result("Log Files Created", len(log_files) > 0)
        
    except Exception as e:
        results.add_result("Advanced Logging System", False, e)
    
    return results

def test_api_endpoints():
    """Test API endpoints functionality"""
    print("\n🧪 Testing API Endpoints")
    print("=" * 50)
    
    results = TestResults()
    
    try:
        # Test 1: Health Check Endpoint
        import requests
        try:
            response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
            results.add_result("Health Check Endpoint", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("Health Check Endpoint", False, "Server not running")
        
        # Test 2: Review Queue Stats Endpoint
        try:
            response = requests.get("http://127.0.0.1:8000/api/review-queue/stats", timeout=5)
            results.add_result("Review Queue Stats Endpoint", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("Review Queue Stats Endpoint", False, "Server not running")
        
        # Test 3: Review Queue Filter Endpoint
        try:
            response = requests.get("http://127.0.0.1:8000/api/review-queue/filter?status=pending", timeout=5)
            results.add_result("Review Queue Filter Endpoint", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("Review Queue Filter Endpoint", False, "Server not running")
        
        # Test 4: Review Queue Search Endpoint
        try:
            response = requests.get("http://127.0.0.1:8000/api/review-queue/search?query=test", timeout=5)
            results.add_result("Review Queue Search Endpoint", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("Review Queue Search Endpoint", False, "Server not running")
        
    except Exception as e:
        results.add_result("API Endpoints", False, e)
    
    return results

def test_web_ui_components():
    """Test web UI components and functionality"""
    print("\n🧪 Testing Web UI Components")
    print("=" * 50)
    
    results = TestResults()
    
    try:
        # Test 1: Main Page Accessibility
        import requests
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=5)
            results.add_result("Main Page Accessibility", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("Main Page Accessibility", False, "Server not running")
        
        # Test 2: Review Queue Page Accessibility
        try:
            response = requests.get("http://127.0.0.1:8000/review-queue", timeout=5)
            results.add_result("Review Queue Page Accessibility", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("Review Queue Page Accessibility", False, "Server not running")
        
        # Test 3: Static Files Accessibility
        try:
            response = requests.get("http://127.0.0.1:8000/static/style.css", timeout=5)
            results.add_result("CSS File Accessibility", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("CSS File Accessibility", False, "Server not running")
        
        try:
            response = requests.get("http://127.0.0.1:8000/static/app.js", timeout=5)
            results.add_result("JavaScript File Accessibility", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("JavaScript File Accessibility", False, "Server not running")
        
        try:
            response = requests.get("http://127.0.0.1:8000/static/review_queue.js", timeout=5)
            results.add_result("Review Queue JS File Accessibility", response.status_code == 200)
        except requests.exceptions.ConnectionError:
            results.add_result("Review Queue JS File Accessibility", False, "Server not running")
        
    except Exception as e:
        results.add_result("Web UI Components", False, e)
    
    return results

async def test_integration_scenarios():
    """Test integration scenarios between components"""
    print("\n🧪 Testing Integration Scenarios")
    print("=" * 50)
    
    results = TestResults()
    
    try:
        # Test 1: Workflow Executor with Review Queue Integration
        executor = WorkflowExecutor()
        queue = ReviewQueue()
        
        # Inject dependencies
        executor.review_queue = queue
        
        # Test review item creation during workflow execution
        action_data = {
            "workflow_id": "test_workflow_integration",
            "step_number": 1,
            "action_type": "click",
            "reason": "Integration test action",
            "confidence": 0.3
        }
        review_result = await executor._handle_human_review(action_data)
        
        results.add_result("Workflow-ReviewQueue Integration", review_result is not None)
        
        # Test 2: Review Queue with Enhanced Features
        enhanced_item = queue.add_review_item(
            workflow_id="integration_test",
            step_number=1,
            action_type="type",
            action_data={"text": "integration test"},
            reason="Integration test with enhanced features",
            category=ReviewCategory.USER_EXPERIENCE,
            tags=["integration", "test"]
        )
        
        results.add_result("Enhanced Review Item Integration", enhanced_item is not None)
        results.add_result("Category Assignment Integration", enhanced_item.category == ReviewCategory.USER_EXPERIENCE)
        
        # Test 3: Logging Integration
        from utils.log_utils import log_workflow_step
        
        # This should not raise an exception
        log_workflow_step("integration_test", "Test step", "info", {"test": "data"})
        results.add_result("Logging Integration", True)
        
        # Test 4: Performance Monitoring Integration
        with performance_logger("integration_test"):
            time.sleep(0.05)  # Simulate some work
        
        results.add_result("Performance Monitoring Integration", True)
        
    except Exception as e:
        results.add_result("Integration Scenarios", False, e)
    
    return results

async def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Comprehensive Test Suite for Claude Automation Hub")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_results = []
    
    # Run all test suites
    test_suites = [
        ("Workflow Executor Error Handling", test_workflow_executor_error_handling, False),
        ("Review Queue Enhancements", test_review_queue_enhancements, False),
        ("Advanced Logging System", test_logging_system, False),
        ("API Endpoints", test_api_endpoints, False),
        ("Web UI Components", test_web_ui_components, False),
        ("Integration Scenarios", test_integration_scenarios, True)
    ]
    
    for suite_name, test_function, is_async in test_suites:
        print(f"\n📋 Running {suite_name} Tests...")
        try:
            if is_async:
                results = await test_function()
            else:
                results = test_function()
            all_results.append((suite_name, results))
        except Exception as e:
            print(f"❌ Test suite {suite_name} failed with error: {e}")
            # Create empty results for failed suite
            empty_results = TestResults()
            empty_results.add_result(f"{suite_name} Suite", False, e)
            all_results.append((suite_name, empty_results))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for suite_name, results in all_results:
        print(f"\n📋 {suite_name}:")
        print(f"   Total Tests: {results.total_tests}")
        print(f"   Passed: {results.passed_tests}")
        print(f"   Failed: {results.failed_tests}")
        print(f"   Success Rate: {(results.passed_tests/results.total_tests*100):.1f}%" if results.total_tests > 0 else "   Success Rate: N/A")
        
        total_tests += results.total_tests
        total_passed += results.passed_tests
        total_failed += results.failed_tests
    
    print("\n" + "=" * 60)
    print("🎯 OVERALL RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Overall Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "Overall Success Rate: N/A")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! The system is working correctly.")
    else:
        print(f"\n⚠️  {total_failed} tests failed. Please review the errors above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return total_failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_tests())
    sys.exit(0 if success else 1)
