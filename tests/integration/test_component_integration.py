"""
Component Integration Tests

Tests integration between different components of the system.
"""

import pytest
import asyncio
import logging
from typing import Dict, Any, List
import time

from tests.integration.integration_test_base import IntegrationTestBase
from tests.integration.mock_components import MockBrowserController, MockOrchestrator
from core.workflow_executor import WorkflowExecutor
from core.review_queue import ReviewQueue

logger = logging.getLogger(__name__)


class TestComponentIntegration:
    """Test integration between system components"""
    
    @pytest.fixture
    async def integration_test(self):
        """Setup component integration test"""
        test = IntegrationTestBase()
        await test.setup(error_rate=0.1, success_rate=0.9)
        yield test
        await test.teardown()
    
    @pytest.mark.asyncio
    async def test_workflow_executor_browser_integration(self, integration_test):
        """Test integration between WorkflowExecutor and BrowserController"""
        logger.info("Testing WorkflowExecutor-BrowserController integration")
        
        # Test basic browser operations through workflow executor
        workflow_executor = integration_test.workflow_executor
        browser_controller = integration_test.browser_controller
        
        # Execute a simple workflow
        result = await workflow_executor.execute_workflow("Test browser integration")
        
        # Verify browser actions were performed
        browser_history = browser_controller.get_action_history()
        assert len(browser_history) > 0, "No browser actions performed"
        
        # Verify workflow result
        assert result["success"] is True, "Workflow execution failed"
        assert "steps_completed" in result, "Steps completed not reported"
        
        logger.info(f"Browser integration test passed: {len(browser_history)} actions performed")
    
    @pytest.mark.asyncio
    async def test_workflow_executor_orchestrator_integration(self, integration_test):
        """Test integration between WorkflowExecutor and Orchestrator"""
        logger.info("Testing WorkflowExecutor-Orchestrator integration")
        
        workflow_executor = integration_test.workflow_executor
        orchestrator = integration_test.orchestrator
        
        # Execute workflow
        result = await workflow_executor.execute_workflow("Test orchestrator integration")
        
        # Verify AI decisions were made
        ai_history = orchestrator.get_decision_history()
        assert len(ai_history) > 0, "No AI decisions made"
        
        # Verify workflow result
        assert result["success"] is True, "Workflow execution failed"
        
        # Check for AI decision types
        decision_types = [decision["action"] for decision in ai_history]
        assert "analyze_page" in decision_types or "decide_next_action" in decision_types, "No AI analysis performed"
        
        logger.info(f"Orchestrator integration test passed: {len(ai_history)} decisions made")
    
    @pytest.mark.asyncio
    async def test_workflow_executor_review_queue_integration(self, integration_test):
        """Test integration between WorkflowExecutor and ReviewQueue"""
        logger.info("Testing WorkflowExecutor-ReviewQueue integration")
        
        workflow_executor = integration_test.workflow_executor
        review_queue = integration_test.review_queue
        
        # Execute workflow that might trigger reviews
        result = await workflow_executor.execute_workflow("Test review queue integration")
        
        # Check review queue state
        review_stats = review_queue.get_queue_stats()
        assert "total_items" in review_stats, "Review queue stats not available"
        
        # Verify workflow result
        assert result["success"] is True, "Workflow execution failed"
        
        # If reviews were created, verify structure
        if review_stats["total_items"] > 0:
            pending_reviews = review_queue.get_pending_reviews()
            assert len(pending_reviews) > 0, "No pending reviews found"
            
            # Verify review item structure
            review = pending_reviews[0]
            required_fields = ["id", "reason", "priority", "category", "workflow_id"]
            for field in required_fields:
                assert field in review, f"Review item missing {field} field"
        
        logger.info(f"Review queue integration test passed: {review_stats['total_items']} reviews")
    
    @pytest.mark.asyncio
    async def test_browser_orchestrator_integration(self, integration_test):
        """Test integration between BrowserController and Orchestrator"""
        logger.info("Testing BrowserController-Orchestrator integration")
        
        browser_controller = integration_test.browser_controller
        orchestrator = integration_test.orchestrator
        
        # Simulate browser state
        await browser_controller.navigate("https://example.com")
        browser_state = browser_controller.get_current_state()
        
        # Simulate AI analysis of browser state
        page_data = {
            "url": browser_state.url,
            "title": browser_state.title,
            "elements": [
                {
                    "tag": elem.tag,
                    "text": elem.text,
                    "xpath": elem.xpath
                }
                for elem in browser_state.elements
            ]
        }
        
        # Test AI analysis
        analysis_result = await orchestrator.analyze_page(page_data)
        assert analysis_result["success"] is True, "AI analysis failed"
        assert "analysis" in analysis_result, "Analysis data not returned"
        
        # Test AI decision making
        context = {
            "page_analysis": analysis_result["analysis"],
            "browser_state": page_data
        }
        
        decision_result = await orchestrator.decide_next_action(context)
        assert decision_result["success"] is True, "AI decision failed"
        assert "action" in decision_result, "Action data not returned"
        
        logger.info("Browser-Orchestrator integration test passed")
    
    @pytest.mark.asyncio
    async def test_review_queue_workflow_integration(self, integration_test):
        """Test integration between ReviewQueue and WorkflowExecutor"""
        logger.info("Testing ReviewQueue-WorkflowExecutor integration")
        
        review_queue = integration_test.review_queue
        workflow_executor = integration_test.workflow_executor
        
        # Add a test review item
        review_id = review_queue.add_review_item(
            reason="Test review integration",
            workflow_id="test_workflow_123",
            step_number=1,
            action_type="click",
            element_selector="//button[@id='test']",
            confidence=0.8
        )
        
        # Verify review was created
        review_stats = review_queue.get_queue_stats()
        assert review_stats["total_items"] == 1, "Review item not created"
        
        # Test review processing
        pending_reviews = review_queue.get_pending_reviews()
        assert len(pending_reviews) == 1, "Pending review not found"
        
        # Submit review
        review_result = review_queue.submit_review(
            review_id=review_id,
            decision=True,
            reviewer_id="test_reviewer",
            notes="Integration test approval"
        )
        
        assert review_result["success"] is True, "Review submission failed"
        
        # Verify review status
        updated_stats = review_queue.get_queue_stats()
        assert updated_stats["approved"] == 1, "Review not marked as approved"
        
        logger.info("Review queue-WorkflowExecutor integration test passed")
    
    @pytest.mark.asyncio
    async def test_error_propagation_integration(self, integration_test):
        """Test error propagation between components"""
        logger.info("Testing error propagation integration")
        
        # Set high error rate
        integration_test.browser_controller.error_rate = 0.8
        integration_test.orchestrator.success_rate = 0.3
        
        workflow_executor = integration_test.workflow_executor
        
        # Execute workflow that should encounter errors
        try:
            result = await workflow_executor.execute_workflow("Error propagation test")
            
            # Should handle errors gracefully
            assert "success" in result, "Result should indicate success/failure"
            
            if not result["success"]:
                assert "error_message" in result, "Error message should be provided"
                logger.info("Error propagation handled correctly")
            else:
                logger.info("Workflow succeeded despite high error rate")
                
        except Exception as e:
            # Errors should be caught and handled by workflow executor
            logger.info(f"Error caught and handled: {e}")
        
        # Reset error rates
        integration_test.browser_controller.error_rate = 0.1
        integration_test.orchestrator.success_rate = 0.9
        
        logger.info("Error propagation integration test completed")
    
    @pytest.mark.asyncio
    async def test_performance_integration(self, integration_test):
        """Test performance integration between components"""
        logger.info("Testing performance integration")
        
        workflow_executor = integration_test.workflow_executor
        
        # Measure execution time
        start_time = time.time()
        
        # Execute multiple workflows
        tasks = []
        for i in range(5):
            task = workflow_executor.execute_workflow(f"Performance test {i+1}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        execution_time = end_time - start_time
        
        # Verify performance
        assert execution_time < 30, f"Execution too slow: {execution_time:.2f}s"
        assert successful >= 3, f"Too many failures: {successful}/5 successful"
        
        logger.info(f"Performance integration test: {successful}/5 successful in {execution_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_data_flow_integration(self, integration_test):
        """Test data flow between components"""
        logger.info("Testing data flow integration")
        
        browser_controller = integration_test.browser_controller
        orchestrator = integration_test.orchestrator
        review_queue = integration_test.review_queue
        
        # Simulate complete data flow
        # 1. Browser action
        await browser_controller.navigate("https://example.com")
        browser_state = browser_controller.get_current_state()
        
        # 2. AI analysis
        page_data = {
            "url": browser_state.url,
            "title": browser_state.title,
            "elements": [{"tag": elem.tag, "text": elem.text, "xpath": elem.xpath} for elem in browser_state.elements]
        }
        
        analysis_result = await orchestrator.analyze_page(page_data)
        assert analysis_result["success"] is True
        
        # 3. AI decision
        context = {"page_analysis": analysis_result["analysis"]}
        decision_result = await orchestrator.decide_next_action(context)
        assert decision_result["success"] is True
        
        # 4. Review queue interaction (if needed)
        if decision_result["action"].get("confidence", 1.0) < 0.8:
            review_id = review_queue.add_review_item(
                reason="Low confidence action",
                workflow_id="data_flow_test",
                step_number=1,
                action_type=decision_result["action"]["action_type"],
                element_selector=decision_result["action"]["target"],
                confidence=decision_result["action"]["confidence"]
            )
            assert review_id is not None
        
        logger.info("Data flow integration test passed")
    
    @pytest.mark.asyncio
    async def test_state_consistency_integration(self, integration_test):
        """Test state consistency across components"""
        logger.info("Testing state consistency integration")
        
        workflow_executor = integration_test.workflow_executor
        browser_controller = integration_test.browser_controller
        review_queue = integration_test.review_queue
        
        # Execute workflow
        result = await workflow_executor.execute_workflow("State consistency test")
        
        # Verify state consistency
        assert result["success"] is True, "Workflow should succeed"
        
        # Check browser state
        browser_state = browser_controller.get_current_state()
        assert browser_state.url is not None, "Browser state should have URL"
        
        # Check review queue state
        review_stats = review_queue.get_queue_stats()
        assert "total_items" in review_stats, "Review queue should have stats"
        
        # Check workflow executor state
        performance_metrics = workflow_executor.get_performance_metrics()
        assert "total_execution_time" in performance_metrics, "Performance metrics should be available"
        
        logger.info("State consistency integration test passed")


class TestComponentIsolation:
    """Test component isolation and independence"""
    
    @pytest.fixture
    async def isolation_test(self):
        """Setup component isolation test"""
        test = IntegrationTestBase()
        await test.setup(error_rate=0.1, success_rate=0.9)
        yield test
        await test.teardown()
    
    @pytest.mark.asyncio
    async def test_browser_controller_isolation(self, isolation_test):
        """Test BrowserController isolation"""
        logger.info("Testing BrowserController isolation")
        
        browser_controller = isolation_test.browser_controller
        
        # Test independent operations
        await browser_controller.navigate("https://example.com")
        await browser_controller.take_screenshot()
        await browser_controller.extract_text()
        
        # Verify state is maintained independently
        browser_state = browser_controller.get_current_state()
        assert browser_state.url == "https://example.com"
        assert browser_state.screenshot_path is not None
        
        # Verify action history
        history = browser_controller.get_action_history()
        assert len(history) == 3, "All actions should be recorded"
        
        logger.info("BrowserController isolation test passed")
    
    @pytest.mark.asyncio
    async def test_orchestrator_isolation(self, isolation_test):
        """Test Orchestrator isolation"""
        logger.info("Testing Orchestrator isolation")
        
        orchestrator = isolation_test.orchestrator
        
        # Test independent operations
        page_data = {"url": "https://example.com", "elements": []}
        analysis_result = await orchestrator.analyze_page(page_data)
        
        context = {"test": "data"}
        decision_result = await orchestrator.decide_next_action(context)
        
        # Verify decisions are independent
        assert analysis_result["success"] is True
        assert decision_result["success"] is True
        
        # Verify decision history
        history = orchestrator.get_decision_history()
        assert len(history) == 2, "All decisions should be recorded"
        
        logger.info("Orchestrator isolation test passed")
    
    @pytest.mark.asyncio
    async def test_review_queue_isolation(self, isolation_test):
        """Test ReviewQueue isolation"""
        logger.info("Testing ReviewQueue isolation")
        
        review_queue = isolation_test.review_queue
        
        # Test independent operations
        review_id = review_queue.add_review_item(
            reason="Isolation test",
            workflow_id="test_workflow",
            step_number=1,
            action_type="click",
            element_selector="//button"
        )
        
        # Verify review was created
        stats = review_queue.get_queue_stats()
        assert stats["total_items"] == 1
        
        # Test review processing
        pending = review_queue.get_pending_reviews()
        assert len(pending) == 1
        
        # Submit review
        result = review_queue.submit_review(
            review_id=review_id,
            decision=True,
            reviewer_id="test_reviewer"
        )
        
        assert result["success"] is True
        
        # Verify final state
        final_stats = review_queue.get_queue_stats()
        assert final_stats["approved"] == 1
        
        logger.info("ReviewQueue isolation test passed")


if __name__ == "__main__":
    # Run component integration tests
    pytest.main([__file__, "-v"])
