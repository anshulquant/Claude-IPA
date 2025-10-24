"""
Debug Integration Test

Simple test to debug the integration framework issues.
"""

import asyncio
import logging
from tests.integration.integration_test_base import WorkflowIntegrationTest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_test():
    """Debug the integration test"""
    logger.info("Starting debug test")
    
    test = WorkflowIntegrationTest()
    await test.setup(error_rate=0.0, success_rate=1.0)
    
    try:
        # Execute workflow
        logger.info("Executing workflow...")
        result = await test.workflow_executor.execute_workflow("Debug test workflow")
        
        # Debug result
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result attributes: {dir(result)}")
        
        if hasattr(result, '__dict__'):
            logger.info(f"Result dict: {result.__dict__}")
        
        # Check specific attributes
        if hasattr(result, 'success'):
            logger.info(f"Success: {result.success}")
        if hasattr(result, 'workflow_id'):
            logger.info(f"Workflow ID: {result.workflow_id}")
        if hasattr(result, 'actions_taken'):
            logger.info(f"Actions taken: {result.actions_taken}")
        if hasattr(result, 'execution_time'):
            logger.info(f"Execution time: {result.execution_time}")
        
        # Test assertions
        try:
            assert hasattr(result, 'success')
            logger.info("✓ Has success attribute")
        except Exception as e:
            logger.error(f"✗ Missing success attribute: {e}")
        
        try:
            assert hasattr(result, 'workflow_id')
            logger.info("✓ Has workflow_id attribute")
        except Exception as e:
            logger.error(f"✗ Missing workflow_id attribute: {e}")
        
        try:
            assert hasattr(result, 'execution_time')
            logger.info("✓ Has execution_time attribute")
        except Exception as e:
            logger.error(f"✗ Missing execution_time attribute: {e}")
        
        try:
            assert hasattr(result, 'actions_taken')
            logger.info("✓ Has actions_taken attribute")
        except Exception as e:
            logger.error(f"✗ Missing actions_taken attribute: {e}")
        
        # Test success value
        try:
            assert result.success is True
            logger.info("✓ Success is True")
        except Exception as e:
            logger.error(f"✗ Success is not True: {e}")
        
        # Test workflow_id value
        try:
            assert result.workflow_id is not None
            logger.info("✓ Workflow ID is not None")
        except Exception as e:
            logger.error(f"✗ Workflow ID is None: {e}")
        
        # Test actions_taken value
        try:
            assert result.actions_taken > 0
            logger.info("✓ Actions taken > 0")
        except Exception as e:
            logger.error(f"✗ Actions taken <= 0: {e}")
        
        logger.info("Debug test completed successfully")
        
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await test.teardown()

if __name__ == "__main__":
    asyncio.run(debug_test())
