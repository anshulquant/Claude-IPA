#!/usr/bin/env python3
"""
Quick test for the form filling workflow.
"""

import asyncio
from workflows.form_filling import FormFillingWorkflow


async def test_form_filling():
    """Test the form filling workflow with httpbin test form."""
    print("Testing Form Filling Workflow...")
    print("="*60)
    
    workflow = FormFillingWorkflow(headless=False)
    
    # Test with httpbin form
    form_url = "https://httpbin.org/forms/post"
    goal = "Fill out the pizza order form with test data and submit it"
    
    result = await workflow.execute(form_url, goal)
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Steps Executed: {result['steps_executed']}")
    print(f"Final URL: {result.get('final_url', 'N/A')}")
    print("="*60)
    
    return result


if __name__ == "__main__":
    asyncio.run(test_form_filling())
