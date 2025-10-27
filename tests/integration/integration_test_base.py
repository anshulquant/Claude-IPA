"""
Integration Test Base Classes

Provides base classes and utilities for comprehensive integration testing.
"""

import asyncio
import pytest
import logging
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock
import time
import json
import os

from tests.integration.mock_components import MockBrowserController, MockOrchestrator
from core.workflow_executor import WorkflowExecutor
from core.review_queue import ReviewQueue
from api.main import app
from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)


class IntegrationTestBase:
    """Base class for integration tests"""
    
    def __init__(self):
        self.browser_controller = None
        self.orchestrator = None
        self.workflow_executor = None
        self.review_queue = None
        self.test_client = None
        self.setup_complete = False
        
    async def setup(self, error_rate: float = 0.1, success_rate: float = 0.9):
        """Setup test environment with mock components"""
        try:
            # Initialize mock components
            self.browser_controller = MockBrowserController(error_rate=error_rate)
            self.orchestrator = MockOrchestrator(success_rate=success_rate)
            
            # Initialize real components
            self.review_queue = ReviewQueue()
            self.workflow_executor = WorkflowExecutor()
            
            # Inject mock dependencies
            self.workflow_executor.browser_controller = self.browser_controller
            self.workflow_executor.orchestrator = self.orchestrator
            self.workflow_executor.review_queue = self.review_queue
            
            # Setup FastAPI test client
            self.test_client = TestClient(app)
            
            self.setup_complete = True
            logger.info("Integration test setup completed successfully")
            
        except Exception as e:
            logger.error(f"Integration test setup failed: {e}")
            raise
    
    async def teardown(self):
        """Cleanup test environment"""
        try:
            if self.browser_controller:
                self.browser_controller.reset()
            if self.orchestrator:
                self.orchestrator.reset()
            if self.review_queue:
                # Clear review queue
                pass
                
            self.setup_complete = False
            logger.info("Integration test teardown completed")
            
        except Exception as e:
            logger.error(f"Integration test teardown failed: {e}")
    
    def assert_setup(self):
        """Assert that setup is complete"""
        assert self.setup_complete, "Test setup not completed. Call setup() first."
        assert self.browser_controller is not None, "Browser controller not initialized"
        assert self.orchestrator is not None, "Orchestrator not initialized"
        assert self.workflow_executor is not None, "Workflow executor not initialized"
        assert self.review_queue is not None, "Review queue not initialized"
        assert self.test_client is not None, "Test client not initialized"


class WorkflowIntegrationTest(IntegrationTestBase):
    """Integration tests for workflow execution"""
    
    async def test_complete_workflow_execution(self, goal: str = "Test automation workflow"):
        """Test complete workflow execution with mock components"""
        self.assert_setup()
        
        logger.info(f"Starting complete workflow test: {goal}")
        
        try:
            # Execute workflow
            result = await self.workflow_executor.execute_workflow(goal)
            
            # Verify result structure (WorkflowResult is a dataclass)
            assert hasattr(result, 'success')
            assert hasattr(result, 'workflow_id')
            assert hasattr(result, 'execution_time')
            assert hasattr(result, 'actions_taken')
            
            # Verify workflow was executed
            assert result.success is True
            assert result.workflow_id is not None
            assert result.actions_taken > 0
            
            # Verify browser actions were performed
            browser_history = self.browser_controller.get_action_history()
            assert len(browser_history) > 0, "No browser actions performed"
            
            # Verify AI decisions were made
            ai_history = self.orchestrator.get_decision_history()
            assert len(ai_history) > 0, "No AI decisions made"
            
            logger.info(f"Complete workflow test passed: {result.actions_taken} actions")
            return result
            
        except Exception as e:
            logger.error(f"Complete workflow test failed: {e}")
            raise
    
    async def test_workflow_with_errors(self, error_rate: float = 0.5):
        """Test workflow execution with high error rate"""
        self.assert_setup()
        
        # Reset with high error rate
        self.browser_controller.error_rate = error_rate
        self.orchestrator.success_rate = 1.0 - error_rate
        
        logger.info(f"Starting error-prone workflow test (error rate: {error_rate})")
        
        try:
            result = await self.workflow_executor.execute_workflow("Error test workflow")
            
            # Should handle errors gracefully
            assert hasattr(result, 'success')
            assert hasattr(result, 'error_message') or result.success is True
            
            # Check error handling
            if not result.success:
                assert result.error_message is not None
                logger.info("Workflow failed as expected with high error rate")
            else:
                logger.info("Workflow succeeded despite high error rate")
            
            return result
            
        except Exception as e:
            logger.error(f"Error-prone workflow test failed: {e}")
            raise
    
    async def test_workflow_review_integration(self, goal: str = "Test review workflow"):
        """Test workflow with human review integration"""
        self.assert_setup()
        
        logger.info(f"Starting review integration test: {goal}")
        
        try:
            # Execute workflow that should trigger reviews
            result = await self.workflow_executor.execute_workflow(goal)
            
            # Check if reviews were created
            review_stats = self.review_queue.get_queue_stats()
            assert review_stats["total_items"] >= 0, "Review queue stats not available"
            
            # Verify workflow result
            assert result.success is True, "Workflow should succeed"
            
            # If reviews were created, verify they have proper structure
            if review_stats["total_items"] > 0:
                pending_reviews = self.review_queue.get_pending_reviews()
                assert len(pending_reviews) > 0, "No pending reviews found"
                
                # Verify review item structure
                review = pending_reviews[0]
                assert "id" in review
                assert "reason" in review
                assert "priority" in review
                assert "category" in review
                
                logger.info(f"Review integration test passed: {review_stats['total_items']} reviews created")
            
            return result
            
        except Exception as e:
            logger.error(f"Review integration test failed: {e}")
            raise


class APIIntegrationTest(IntegrationTestBase):
    """Integration tests for API endpoints"""
    
    async def test_api_workflow_execution(self, goal: str = "Test API workflow"):
        """Test workflow execution via API"""
        self.assert_setup()
        
        logger.info(f"Starting API workflow test: {goal}")
        
        try:
            # Test workflow execution endpoint
            response = self.test_client.post("/api/workflow/execute", json={
                "goal": goal,
                "start_url": "https://example.com"
            })
            
            assert response.status_code == 200, f"API request failed: {response.status_code}"
            
            data = response.json()
            assert data["success"] is True, f"Workflow execution failed: {data.get('message', 'Unknown error')}"
            assert "workflow_id" in data, "Workflow ID not returned"
            
            # Test status endpoint
            workflow_id = data["workflow_id"]
            status_response = self.test_client.get(f"/api/workflow/{workflow_id}/status")
            
            assert status_response.status_code == 200, "Status endpoint failed"
            status_data = status_response.json()
            assert "status" in status_data, "Status not returned"
            
            logger.info(f"API workflow test passed: {workflow_id}")
            return data
            
        except Exception as e:
            logger.error(f"API workflow test failed: {e}")
            raise
    
    async def test_api_review_queue_integration(self):
        """Test review queue API integration"""
        self.assert_setup()
        
        logger.info("Starting API review queue test")
        
        try:
            # Test review queue stats endpoint
            stats_response = self.test_client.get("/api/review-queue/stats")
            assert stats_response.status_code == 200, "Stats endpoint failed"
            
            stats_data = stats_response.json()
            assert stats_data["success"] is True, "Stats request failed"
            assert "stats" in stats_data, "Stats data not returned"
            
            # Test pending reviews endpoint
            pending_response = self.test_client.get("/api/review-queue/pending")
            assert pending_response.status_code == 200, "Pending reviews endpoint failed"
            
            pending_data = pending_response.json()
            assert pending_data["success"] is True, "Pending reviews request failed"
            assert "pending_reviews" in pending_data, "Pending reviews not returned"
            
            # Test filter endpoint
            filter_response = self.test_client.get("/api/review-queue/filter?status=pending")
            assert filter_response.status_code == 200, "Filter endpoint failed"
            
            filter_data = filter_response.json()
            assert filter_data["success"] is True, "Filter request failed"
            
            logger.info("API review queue test passed")
            return {
                "stats": stats_data,
                "pending": pending_data,
                "filter": filter_data
            }
            
        except Exception as e:
            logger.error(f"API review queue test failed: {e}")
            raise


class PerformanceIntegrationTest(IntegrationTestBase):
    """Integration tests for performance and load testing"""
    
    async def test_concurrent_workflow_execution(self, num_workflows: int = 5):
        """Test concurrent workflow execution"""
        self.assert_setup()
        
        logger.info(f"Starting concurrent workflow test: {num_workflows} workflows")
        
        try:
            # Create multiple workflow tasks
            tasks = []
            for i in range(num_workflows):
                task = self.workflow_executor.execute_workflow(f"Concurrent workflow {i+1}")
                tasks.append(task)
            
            # Execute all workflows concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
            failed = len(results) - successful
            execution_time = end_time - start_time
            
            logger.info(f"Concurrent test completed: {successful} successful, {failed} failed in {execution_time:.2f}s")
            
            # Verify at least some workflows succeeded
            assert successful > 0, "No workflows succeeded in concurrent test"
            
            return {
                "total_workflows": num_workflows,
                "successful": successful,
                "failed": failed,
                "execution_time": execution_time,
                "throughput": num_workflows / execution_time
            }
            
        except Exception as e:
            logger.error(f"Concurrent workflow test failed: {e}")
            raise
    
    async def test_memory_usage_during_execution(self, duration: int = 30):
        """Test memory usage during extended execution"""
        self.assert_setup()
        
        logger.info(f"Starting memory usage test: {duration}s duration")
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            memory_samples = []
            
            # Run workflows for specified duration
            while time.time() - start_time < duration:
                try:
                    await self.workflow_executor.execute_workflow("Memory test workflow")
                    
                    # Sample memory usage
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_samples.append({
                        "timestamp": time.time() - start_time,
                        "memory_mb": current_memory
                    })
                    
                    await asyncio.sleep(1)  # Sample every second
                    
                except Exception as e:
                    logger.warning(f"Workflow failed during memory test: {e}")
                    continue
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            max_memory = max(sample["memory_mb"] for sample in memory_samples)
            
            memory_increase = final_memory - initial_memory
            memory_growth_rate = memory_increase / duration  # MB/s
            
            logger.info(f"Memory test completed: {memory_increase:.2f}MB increase, max: {max_memory:.2f}MB")
            
            # Check for memory leaks (growth rate should be reasonable)
            assert memory_growth_rate < 10, f"Potential memory leak detected: {memory_growth_rate:.2f}MB/s growth"
            
            return {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "max_memory_mb": max_memory,
                "memory_increase_mb": memory_increase,
                "growth_rate_mb_per_sec": memory_growth_rate,
                "samples": memory_samples
            }
            
        except Exception as e:
            logger.error(f"Memory usage test failed: {e}")
            raise


class ErrorIntegrationTest(IntegrationTestBase):
    """Integration tests for error handling and recovery"""
    
    async def test_circuit_breaker_integration(self, failure_threshold: int = 3):
        """Test circuit breaker functionality"""
        self.assert_setup()
        
        logger.info(f"Starting circuit breaker test: {failure_threshold} failure threshold")
        
        try:
            # Set high error rate to trigger circuit breaker
            self.browser_controller.error_rate = 1.0  # 100% error rate
            
            # Execute workflows until circuit breaker opens
            for i in range(failure_threshold + 2):
                try:
                    result = await self.workflow_executor.execute_workflow(f"Circuit breaker test {i+1}")
                    logger.info(f"Workflow {i+1} result: {result.get('success', False)}")
                except Exception as e:
                    logger.info(f"Workflow {i+1} failed as expected: {e}")
            
            # Check circuit breaker status
            circuit_breaker_status = self.workflow_executor.get_circuit_breaker_status()
            assert "is_open" in circuit_breaker_status, "Circuit breaker status not available"
            
            if circuit_breaker_status["is_open"]:
                logger.info("Circuit breaker opened as expected")
            else:
                logger.warning("Circuit breaker did not open despite high error rate")
            
            return circuit_breaker_status
            
        except Exception as e:
            logger.error(f"Circuit breaker test failed: {e}")
            raise
    
    async def test_error_recovery_integration(self):
        """Test error recovery mechanisms"""
        self.assert_setup()
        
        logger.info("Starting error recovery test")
        
        try:
            # Start with high error rate
            self.browser_controller.error_rate = 0.8
            
            # Execute workflow (should fail initially)
            try:
                result = await self.workflow_executor.execute_workflow("Error recovery test")
                logger.info(f"Initial workflow result: {result.get('success', False)}")
            except Exception as e:
                logger.info(f"Initial workflow failed as expected: {e}")
            
            # Reduce error rate to simulate recovery
            self.browser_controller.error_rate = 0.1
            
            # Wait for circuit breaker to potentially reset
            await asyncio.sleep(2)
            
            # Try workflow again (should succeed)
            result = await self.workflow_executor.execute_workflow("Error recovery test 2")
            
            assert result["success"] is True, "Workflow should succeed after error recovery"
            
            logger.info("Error recovery test passed")
            return result
            
        except Exception as e:
            logger.error(f"Error recovery test failed: {e}")
            raise


# Utility functions for integration tests
def create_test_scenarios() -> List[Dict[str, Any]]:
    """Create test scenarios for integration testing"""
    return [
        {
            "name": "simple_workflow",
            "goal": "Navigate to website and extract information",
            "expected_steps": 3,
            "error_rate": 0.1
        },
        {
            "name": "complex_workflow",
            "goal": "Complete multi-step form with validation",
            "expected_steps": 5,
            "error_rate": 0.2
        },
        {
            "name": "error_prone_workflow",
            "goal": "Test error handling and recovery",
            "expected_steps": 2,
            "error_rate": 0.7
        },
        {
            "name": "review_workflow",
            "goal": "Perform actions requiring human review",
            "expected_steps": 4,
            "error_rate": 0.1
        }
    ]


def generate_test_report(test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive test report"""
    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results if r.get("success", False))
    failed_tests = total_tests - successful_tests
    
    return {
        "summary": {
            "total_tests": total_tests,
            "successful": successful_tests,
            "failed": failed_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0
        },
        "test_results": test_results,
        "timestamp": time.time()
    }
