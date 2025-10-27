#!/usr/bin/env python3
"""
Performance Test Suite for Claude Automation Hub
Tests system performance under various loads and conditions
"""

import asyncio
import time
import psutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.workflow_executor import WorkflowExecutor
from core.review_queue import ReviewQueue, ReviewCategory, ReviewPriority
from utils.log_utils import MemoryMonitor, performance_logger

class PerformanceTester:
    def __init__(self):
        self.results = []
        self.memory_monitor = MemoryMonitor()
    
    def log_performance(self, test_name, duration, memory_usage, success=True):
        """Log performance test results"""
        self.results.append({
            'test': test_name,
            'duration': duration,
            'memory_usage': memory_usage,
            'success': success,
            'timestamp': datetime.now()
        })
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {duration:.3f}s, {memory_usage:.1f}MB")
    
    def test_review_queue_performance(self):
        """Test review queue performance with large datasets"""
        print("\n⚡ Testing Review Queue Performance")
        print("-" * 40)
        
        start_time = time.time()
        start_memory = self.memory_monitor.get_memory_usage()
        
        try:
            queue = ReviewQueue()
            
            # Test 1: Bulk Review Item Creation
            bulk_start = time.time()
            review_items = []
            
            for i in range(1000):  # Create 1000 review items
                item = queue.add_review_item(
                    workflow_id=f"perf_test_{i}",
                    step_number=i % 10,
                    action_type="click",
                    reason=f"Performance test item {i}",
                    confidence=0.5,
                    category=ReviewCategory.OTHER,
                    tags=[f"perf_test_{i % 10}"],
                    estimated_review_time=2
                )
                review_items.append(item)
            
            bulk_duration = time.time() - bulk_start
            bulk_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Bulk Review Item Creation (1000 items)", 
                bulk_duration, 
                bulk_memory - start_memory
            )
            
            # Test 2: Filtering Performance
            filter_start = time.time()
            
            # Test various filters
            security_reviews = queue.filter_reviews(category=ReviewCategory.SECURITY)
            high_priority = queue.filter_reviews(priority=ReviewPriority.HIGH)
            pending_reviews = queue.filter_reviews(status="pending")
            
            filter_duration = time.time() - filter_start
            filter_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Review Filtering (3 filters on 1000 items)", 
                filter_duration, 
                filter_memory - bulk_memory
            )
            
            # Test 3: Search Performance
            search_start = time.time()
            
            # Test multiple searches
            for i in range(0, 1000, 100):  # Search every 100th item
                results = queue.search_reviews(f"perf_test_{i}")
            
            search_duration = time.time() - search_start
            search_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Review Search (10 searches on 1000 items)", 
                search_duration, 
                search_memory - filter_memory
            )
            
            # Test 4: Batch Operations Performance
            batch_start = time.time()
            
            # Select first 100 items for batch operations
            selected_ids = [item.id for item in review_items[:100]]
            
            # Batch approve
            queue.batch_approve(selected_ids[:50], "perf_tester", "Performance test approval")
            
            # Batch reject
            queue.batch_reject(selected_ids[50:], "perf_tester", "Performance test rejection")
            
            batch_duration = time.time() - batch_start
            batch_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Batch Operations (100 items)", 
                batch_duration, 
                batch_memory - search_memory
            )
            
            # Test 5: Export Performance
            export_start = time.time()
            
            export_file = queue.export_review_data("performance_test_export.json")
            
            export_duration = time.time() - export_start
            export_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Data Export (1000 items)", 
                export_duration, 
                export_memory - batch_memory
            )
            
            # Cleanup
            if Path("performance_test_export.json").exists():
                Path("performance_test_export.json").unlink()
            
            total_duration = time.time() - start_time
            total_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Total Review Queue Performance Test", 
                total_duration, 
                total_memory - start_memory
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            memory = self.memory_monitor.get_memory_usage()
            self.log_performance("Review Queue Performance Test", duration, memory, False)
            print(f"   Error: {e}")
            return False
    
    def test_workflow_executor_performance(self):
        """Test workflow executor performance"""
        print("\n⚡ Testing Workflow Executor Performance")
        print("-" * 40)
        
        start_time = time.time()
        start_memory = self.memory_monitor.get_memory_usage()
        
        try:
            executor = WorkflowExecutor()
            
            # Test 1: Performance Metrics Tracking
            metrics_start = time.time()
            
            # Simulate multiple workflow steps
            for i in range(100):
                executor._update_performance_metrics(0.1, True, 0)
            
            metrics_duration = time.time() - metrics_start
            metrics_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Performance Metrics Tracking (100 updates)", 
                metrics_duration, 
                metrics_memory - start_memory
            )
            
            # Test 2: Error Classification Performance
            error_start = time.time()
            
            test_errors = [
                Exception("Network timeout"),
                Exception("Connection refused"),
                Exception("Invalid credentials"),
                Exception("Permission denied"),
                Exception("File not found")
            ]
            
            for _ in range(1000):  # Test 1000 error classifications
                for error in test_errors:
                    executor._classify_error(error)
            
            error_duration = time.time() - error_start
            error_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Error Classification (5000 classifications)", 
                error_duration, 
                error_memory - metrics_memory
            )
            
            # Test 3: Retry Delay Calculation Performance
            retry_start = time.time()
            
            from core.workflow_executor import RetryConfig
            retry_config = RetryConfig()
            
            for i in range(1000):  # Test 1000 retry delay calculations
                executor._calculate_retry_delay(i % 10, retry_config)
            
            retry_duration = time.time() - retry_start
            retry_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Retry Delay Calculation (1000 calculations)", 
                retry_duration, 
                retry_memory - error_memory
            )
            
            total_duration = time.time() - start_time
            total_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Total Workflow Executor Performance Test", 
                total_duration, 
                total_memory - start_memory
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            memory = self.memory_monitor.get_memory_usage()
            self.log_performance("Workflow Executor Performance Test", duration, memory, False)
            print(f"   Error: {e}")
            return False
    
    def test_concurrent_operations(self):
        """Test concurrent operations performance"""
        print("\n⚡ Testing Concurrent Operations Performance")
        print("-" * 40)
        
        start_time = time.time()
        start_memory = self.memory_monitor.get_memory_usage()
        
        try:
            queue = ReviewQueue()
            
            def create_review_items(thread_id, count):
                """Create review items in a thread"""
                items = []
                for i in range(count):
                    item = queue.add_review_item(
                        workflow_id=f"concurrent_test_{thread_id}_{i}",
                        step_number=i,
                        action_type="click",
                        reason=f"Concurrent test item {thread_id}-{i}",
                        confidence=0.5,
                        category=ReviewCategory.OTHER
                    )
                    items.append(item)
                return items
            
            # Test 1: Concurrent Review Item Creation
            concurrent_start = time.time()
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i in range(5):  # 5 threads
                    future = executor.submit(create_review_items, i, 100)  # 100 items per thread
                    futures.append(future)
                
                # Wait for all threads to complete
                all_items = []
                for future in futures:
                    all_items.extend(future.result())
            
            concurrent_duration = time.time() - concurrent_start
            concurrent_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Concurrent Review Item Creation (5 threads, 500 items)", 
                concurrent_duration, 
                concurrent_memory - start_memory
            )
            
            # Test 2: Concurrent Filtering
            filter_start = time.time()
            
            def filter_reviews_thread(thread_id):
                """Filter reviews in a thread"""
                results = []
                for i in range(10):  # 10 filter operations per thread
                    filtered = queue.filter_reviews(workflow_id=f"concurrent_test_{thread_id}")
                    results.append(len(filtered))
                return results
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i in range(3):  # 3 threads
                    future = executor.submit(filter_reviews_thread, i)
                    futures.append(future)
                
                # Wait for all threads to complete
                for future in futures:
                    future.result()
            
            filter_duration = time.time() - filter_start
            filter_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Concurrent Review Filtering (3 threads, 30 operations)", 
                filter_duration, 
                filter_memory - concurrent_memory
            )
            
            total_duration = time.time() - start_time
            total_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Total Concurrent Operations Test", 
                total_duration, 
                total_memory - start_memory
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            memory = self.memory_monitor.get_memory_usage()
            self.log_performance("Concurrent Operations Test", duration, memory, False)
            print(f"   Error: {e}")
            return False
    
    def test_memory_usage(self):
        """Test memory usage patterns"""
        print("\n⚡ Testing Memory Usage Patterns")
        print("-" * 40)
        
        start_time = time.time()
        start_memory = self.memory_monitor.get_memory_usage()
        
        try:
            queue = ReviewQueue()
            
            # Test 1: Memory Growth with Item Creation
            memory_measurements = []
            
            for i in range(0, 1001, 100):  # Measure every 100 items
                if i > 0:
                    # Create 100 items
                    for j in range(100):
                        queue.add_review_item(
                            workflow_id=f"memory_test_{i}_{j}",
                            step_number=j,
                            action_type="click",
                            reason=f"Memory test item {i}-{j}",
                            confidence=0.5,
                            category=ReviewCategory.OTHER
                        )
                
                current_memory = self.memory_monitor.get_memory_usage()
                memory_measurements.append({
                    'items': i,
                    'memory': current_memory,
                    'memory_growth': current_memory - start_memory
                })
            
            # Calculate memory growth rate
            if len(memory_measurements) > 1:
                memory_growth = memory_measurements[-1]['memory_growth']
                items_created = memory_measurements[-1]['items']
                growth_per_item = memory_growth / items_created if items_created > 0 else 0
                
                self.log_performance(
                    f"Memory Growth Analysis ({items_created} items)", 
                    0,  # No time measurement for this test
                    memory_growth
                )
                
                print(f"   Memory growth per item: {growth_per_item:.4f}MB")
                print(f"   Total memory growth: {memory_growth:.2f}MB")
            
            # Test 2: Memory Cleanup
            cleanup_start = time.time()
            
            # Clear all items
            all_items = queue.filter_reviews()
            for item in all_items:
                queue.submit_review(item.id, False, "cleanup", "Memory test cleanup")
            
            cleanup_duration = time.time() - cleanup_start
            cleanup_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Memory Cleanup", 
                cleanup_duration, 
                cleanup_memory - start_memory
            )
            
            total_duration = time.time() - start_time
            total_memory = self.memory_monitor.get_memory_usage()
            
            self.log_performance(
                "Total Memory Usage Test", 
                total_duration, 
                total_memory - start_memory
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            memory = self.memory_monitor.get_memory_usage()
            self.log_performance("Memory Usage Test", duration, memory, False)
            print(f"   Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 Performance Test Suite for Claude Automation Hub")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all performance tests
        test_functions = [
            self.test_review_queue_performance,
            self.test_workflow_executor_performance,
            self.test_concurrent_operations,
            self.test_memory_usage
        ]
        
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed: {e}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print performance test summary"""
        print("\n" + "=" * 60)
        print("📊 Performance Test Results Summary")
        print("=" * 60)
        
        if not self.results:
            print("No performance tests completed.")
            return
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        # Performance metrics
        durations = [r['duration'] for r in self.results if r['success'] and r['duration'] > 0]
        memory_usages = [r['memory_usage'] for r in self.results if r['success']]
        
        if durations:
            print(f"\n⏱️  Performance Metrics:")
            print(f"   Average Duration: {sum(durations)/len(durations):.3f}s")
            print(f"   Max Duration: {max(durations):.3f}s")
            print(f"   Min Duration: {min(durations):.3f}s")
        
        if memory_usages:
            print(f"\n💾 Memory Usage:")
            print(f"   Average Memory: {sum(memory_usages)/len(memory_usages):.1f}MB")
            print(f"   Max Memory: {max(memory_usages):.1f}MB")
            print(f"   Min Memory: {min(memory_usages):.1f}MB")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if failed_tests == 0:
            print("\n🎉 All performance tests completed successfully!")
        else:
            print(f"\n⚠️  {failed_tests} performance tests failed.")

def main():
    """Main function to run performance tests"""
    tester = PerformanceTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
