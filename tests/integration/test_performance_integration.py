"""
Performance Integration Tests

Comprehensive performance testing for the integration framework.
"""

import pytest
import asyncio
import logging
import time
import psutil
import os
from typing import Dict, Any, List
import statistics

from tests.integration.integration_test_base import PerformanceIntegrationTest
from tests.integration.mock_components import MockBrowserController, MockOrchestrator

logger = logging.getLogger(__name__)


class TestPerformanceIntegration:
    """Performance integration tests"""
    
    @pytest.fixture
    async def perf_test(self):
        """Setup performance test"""
        test = PerformanceIntegrationTest()
        await test.setup(error_rate=0.1, success_rate=0.9)
        yield test
        await test.teardown()
    
    @pytest.mark.asyncio
    async def test_single_workflow_performance(self, perf_test):
        """Test performance of single workflow execution"""
        logger.info("Testing single workflow performance")
        
        start_time = time.time()
        result = await perf_test.test_complete_workflow_execution("Single workflow performance test")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 10, f"Single workflow too slow: {execution_time:.2f}s"
        assert result["success"] is True, "Workflow should succeed"
        
        # Check performance metrics
        metrics = perf_test.workflow_executor.get_performance_metrics()
        assert "total_execution_time" in metrics
        assert metrics["total_execution_time"] > 0
        
        logger.info(f"Single workflow performance: {execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, perf_test):
        """Test performance under concurrent load"""
        logger.info("Testing concurrent workflow performance")
        
        # Test different concurrency levels
        concurrency_levels = [2, 5, 10]
        results = {}
        
        for num_workflows in concurrency_levels:
            start_time = time.time()
            result = await perf_test.test_concurrent_workflow_execution(num_workflows)
            end_time = time.time()
            
            execution_time = end_time - start_time
            throughput = num_workflows / execution_time
            
            results[num_workflows] = {
                "execution_time": execution_time,
                "throughput": throughput,
                "success_rate": result["successful"] / num_workflows
            }
            
            # Performance assertions
            assert execution_time < 30, f"Concurrent execution too slow: {execution_time:.2f}s"
            assert throughput > 0.1, f"Throughput too low: {throughput:.2f} workflows/s"
            assert result["successful"] >= num_workflows * 0.7, f"Success rate too low: {result['successful']}/{num_workflows}"
        
        logger.info(f"Concurrent performance results: {results}")
    
    @pytest.mark.asyncio
    async def test_memory_performance(self, perf_test):
        """Test memory usage performance"""
        logger.info("Testing memory performance")
        
        result = await perf_test.test_memory_usage_during_execution(duration=15)
        
        # Memory performance assertions
        assert result["growth_rate_mb_per_sec"] < 5, f"Memory leak detected: {result['growth_rate_mb_per_sec']:.2f}MB/s"
        assert result["max_memory_mb"] < 1000, f"Memory usage too high: {result['max_memory_mb']:.2f}MB"
        
        # Check memory samples
        assert len(result["samples"]) > 0, "No memory samples collected"
        
        # Calculate memory stability
        memory_values = [sample["memory_mb"] for sample in result["samples"]]
        memory_variance = statistics.variance(memory_values) if len(memory_values) > 1 else 0
        
        assert memory_variance < 100, f"Memory usage too variable: {memory_variance:.2f}"
        
        logger.info(f"Memory performance: {result['growth_rate_mb_per_sec']:.2f}MB/s growth, max: {result['max_memory_mb']:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_browser_controller_performance(self, perf_test):
        """Test BrowserController performance"""
        logger.info("Testing BrowserController performance")
        
        browser_controller = perf_test.browser_controller
        
        # Test individual operations
        operations = [
            ("navigate", lambda: browser_controller.navigate("https://example.com")),
            ("screenshot", lambda: browser_controller.take_screenshot()),
            ("extract_text", lambda: browser_controller.extract_text()),
            ("extract_elements", lambda: browser_controller.extract_elements("button")),
            ("click", lambda: browser_controller.click("//button[@id='test']"))
        ]
        
        operation_times = {}
        
        for op_name, op_func in operations:
            start_time = time.time()
            await op_func()
            end_time = time.time()
            
            operation_time = end_time - start_time
            operation_times[op_name] = operation_time
            
            # Performance assertions
            assert operation_time < 2, f"{op_name} too slow: {operation_time:.2f}s"
        
        # Test batch operations
        start_time = time.time()
        batch_tasks = [op_func() for _, op_func in operations]
        await asyncio.gather(*batch_tasks)
        end_time = time.time()
        
        batch_time = end_time - start_time
        assert batch_time < 5, f"Batch operations too slow: {batch_time:.2f}s"
        
        logger.info(f"BrowserController performance: {operation_times}")
    
    @pytest.mark.asyncio
    async def test_orchestrator_performance(self, perf_test):
        """Test Orchestrator performance"""
        logger.info("Testing Orchestrator performance")
        
        orchestrator = perf_test.orchestrator
        
        # Test AI operations
        page_data = {
            "url": "https://example.com",
            "elements": [
                {"tag": "button", "text": "Click me", "xpath": "//button"},
                {"tag": "input", "text": "", "xpath": "//input[@type='text']"}
            ]
        }
        
        operations = [
            ("analyze_page", lambda: orchestrator.analyze_page(page_data)),
            ("decide_next_action", lambda: orchestrator.decide_next_action({"page": page_data})),
            ("validate_action", lambda: orchestrator.validate_action({"action_type": "click"}, {"context": "test"})),
            ("generate_workflow_plan", lambda: orchestrator.generate_workflow_plan("Test goal", {"context": "test"}))
        ]
        
        operation_times = {}
        
        for op_name, op_func in operations:
            start_time = time.time()
            result = await op_func()
            end_time = time.time()
            
            operation_time = end_time - start_time
            operation_times[op_name] = operation_time
            
            # Performance assertions
            assert operation_time < 3, f"{op_name} too slow: {operation_time:.2f}s"
            assert result["success"] is True, f"{op_name} should succeed"
        
        # Test batch AI operations
        start_time = time.time()
        batch_tasks = [op_func() for _, op_func in operations]
        await asyncio.gather(*batch_tasks)
        end_time = time.time()
        
        batch_time = end_time - start_time
        assert batch_time < 8, f"Batch AI operations too slow: {batch_time:.2f}s"
        
        logger.info(f"Orchestrator performance: {operation_times}")
    
    @pytest.mark.asyncio
    async def test_review_queue_performance(self, perf_test):
        """Test ReviewQueue performance"""
        logger.info("Testing ReviewQueue performance")
        
        review_queue = perf_test.review_queue
        
        # Test adding multiple reviews
        start_time = time.time()
        
        review_ids = []
        for i in range(100):
            review_id = review_queue.add_review_item(
                reason=f"Performance test review {i}",
                workflow_id=f"perf_test_{i}",
                step_number=1,
                action_type="click",
                element_selector=f"//button[{i}]"
            )
            review_ids.append(review_id)
        
        add_time = time.time() - start_time
        
        # Test querying reviews
        start_time = time.time()
        
        stats = review_queue.get_queue_stats()
        pending = review_queue.get_pending_reviews()
        filtered = review_queue.filter_reviews(status="pending")
        
        query_time = time.time() - start_time
        
        # Test batch operations
        start_time = time.time()
        
        if len(review_ids) >= 10:
            batch_result = review_queue.batch_approve(
                review_ids[:10],
                reviewer_id="perf_test_reviewer",
                notes="Performance test batch approval"
            )
            assert batch_result["success"] is True
        
        batch_time = time.time() - start_time
        
        # Performance assertions
        assert add_time < 5, f"Adding reviews too slow: {add_time:.2f}s"
        assert query_time < 2, f"Querying reviews too slow: {query_time:.2f}s"
        assert batch_time < 3, f"Batch operations too slow: {batch_time:.2f}s"
        
        # Verify data integrity
        assert len(review_ids) == 100, "Not all reviews created"
        assert stats["total_items"] >= 100, "Review count mismatch"
        
        logger.info(f"ReviewQueue performance: add={add_time:.2f}s, query={query_time:.2f}s, batch={batch_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_system_resource_usage(self, perf_test):
        """Test overall system resource usage"""
        logger.info("Testing system resource usage")
        
        process = psutil.Process(os.getpid())
        
        # Measure baseline
        baseline_cpu = process.cpu_percent()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run intensive operations
        start_time = time.time()
        
        # Execute multiple workflows concurrently
        tasks = []
        for i in range(20):
            task = perf_test.workflow_executor.execute_workflow(f"Resource test {i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Measure peak usage
        peak_cpu = process.cpu_percent()
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Calculate resource usage
        cpu_usage = peak_cpu - baseline_cpu
        memory_usage = peak_memory - baseline_memory
        
        # Performance assertions
        assert execution_time < 60, f"Execution too slow: {execution_time:.2f}s"
        assert cpu_usage < 50, f"CPU usage too high: {cpu_usage:.1f}%"
        assert memory_usage < 200, f"Memory usage too high: {memory_usage:.1f}MB"
        
        # Verify results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        assert successful >= 15, f"Too many failures: {successful}/20"
        
        logger.info(f"Resource usage: CPU={cpu_usage:.1f}%, Memory={memory_usage:.1f}MB, Time={execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_scalability_performance(self, perf_test):
        """Test system scalability"""
        logger.info("Testing scalability performance")
        
        # Test different scales
        scales = [1, 5, 10, 20]
        scale_results = {}
        
        for scale in scales:
            logger.info(f"Testing scale: {scale} workflows")
            
            start_time = time.time()
            
            # Create workflows
            tasks = []
            for i in range(scale):
                task = perf_test.workflow_executor.execute_workflow(f"Scale test {i}")
                tasks.append(task)
            
            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Calculate metrics
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
            throughput = scale / execution_time
            success_rate = successful / scale
            
            scale_results[scale] = {
                "execution_time": execution_time,
                "throughput": throughput,
                "success_rate": success_rate,
                "successful": successful
            }
            
            # Scalability assertions
            assert execution_time < 30, f"Scale {scale} too slow: {execution_time:.2f}s"
            assert success_rate >= 0.7, f"Scale {scale} success rate too low: {success_rate:.2f}"
            assert throughput > 0.1, f"Scale {scale} throughput too low: {throughput:.2f}"
        
        # Analyze scalability trends
        throughputs = [scale_results[s]["throughput"] for s in scales]
        
        # Throughput should not degrade significantly with scale
        max_throughput = max(throughputs)
        min_throughput = min(throughputs)
        throughput_ratio = min_throughput / max_throughput if max_throughput > 0 else 0
        
        assert throughput_ratio > 0.5, f"Throughput degraded too much: {throughput_ratio:.2f}"
        
        logger.info(f"Scalability results: {scale_results}")
    
    @pytest.mark.asyncio
    async def test_stress_performance(self, perf_test):
        """Test system under stress"""
        logger.info("Testing stress performance")
        
        # Set high error rates to simulate stress
        perf_test.browser_controller.error_rate = 0.3
        perf_test.orchestrator.success_rate = 0.7
        
        # Run stress test
        start_time = time.time()
        
        # Execute many workflows with high error rates
        tasks = []
        for i in range(50):
            task = perf_test.workflow_executor.execute_workflow(f"Stress test {i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Analyze results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed = len(results) - successful
        success_rate = successful / len(results)
        
        # Stress test assertions
        assert execution_time < 120, f"Stress test too slow: {execution_time:.2f}s"
        assert success_rate >= 0.3, f"Success rate too low under stress: {success_rate:.2f}"
        
        # System should remain stable
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        assert memory_usage < 500, f"Memory usage too high under stress: {memory_usage:.1f}MB"
        
        logger.info(f"Stress test: {successful}/{len(results)} successful in {execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_performance_regression(self, perf_test):
        """Test for performance regressions"""
        logger.info("Testing performance regression")
        
        # Define performance baselines
        baselines = {
            "single_workflow_time": 5.0,  # seconds
            "concurrent_throughput": 0.5,  # workflows/second
            "memory_growth_rate": 2.0,  # MB/second
            "cpu_usage": 30.0,  # percentage
            "success_rate": 0.8  # percentage
        }
        
        # Test single workflow
        start_time = time.time()
        result = await perf_test.test_complete_workflow_execution("Regression test")
        single_time = time.time() - start_time
        
        assert single_time <= baselines["single_workflow_time"], f"Single workflow regression: {single_time:.2f}s > {baselines['single_workflow_time']}s"
        
        # Test concurrent performance
        concurrent_result = await perf_test.test_concurrent_workflow_execution(10)
        throughput = concurrent_result["total_workflows"] / concurrent_result["execution_time"]
        
        assert throughput >= baselines["concurrent_throughput"], f"Concurrent throughput regression: {throughput:.2f} < {baselines['concurrent_throughput']}"
        
        # Test memory performance
        memory_result = await perf_test.test_memory_usage_during_execution(duration=10)
        
        assert memory_result["growth_rate_mb_per_sec"] <= baselines["memory_growth_rate"], f"Memory growth regression: {memory_result['growth_rate_mb_per_sec']:.2f} > {baselines['memory_growth_rate']}"
        
        # Test success rate
        success_rate = concurrent_result["successful"] / concurrent_result["total_workflows"]
        
        assert success_rate >= baselines["success_rate"], f"Success rate regression: {success_rate:.2f} < {baselines['success_rate']}"
        
        logger.info("Performance regression test passed")


if __name__ == "__main__":
    # Run performance integration tests
    pytest.main([__file__, "-v"])
