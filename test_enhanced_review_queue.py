#!/usr/bin/env python3
"""
Test script for Enhanced Review Queue functionality
Demonstrates the new features and interactive console
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.review_queue import (
    ReviewQueue, 
    ReviewPriority, 
    ReviewCategory, 
    ReviewStatus,
    run_review_console
)

def test_enhanced_review_queue():
    """Test the enhanced review queue functionality"""
    print("🧪 Testing Enhanced Review Queue Features")
    print("=" * 50)
    
    # Create a new review queue instance
    queue = ReviewQueue()
    
    # Test 1: Add review items with different categories and priorities
    print("\n📝 Test 1: Adding Review Items with Enhanced Features")
    print("-" * 50)
    
    # Add a security-related review
    security_review = queue.add_review_item(
        workflow_id="workflow_001",
        step_number=1,
        action_type="login",
        action_data={"username": "test_user", "password": "***"},
        reason="Low confidence login attempt detected",
        priority=ReviewPriority.HIGH,
        category=ReviewCategory.SECURITY,
        context={"ip_address": "192.168.1.100", "user_agent": "Chrome/91.0"},
        tags=["low-confidence", "security-action", "high-risk"],
        estimated_review_time=10
    )
    print(f"✅ Added security review: {security_review}")
    
    # Add a performance-related review
    performance_review = queue.add_review_item(
        workflow_id="workflow_002",
        step_number=3,
        action_type="optimize_page",
        action_data={"page_url": "https://example.com", "load_time": "5.2s"},
        reason="Page load time exceeds threshold",
        priority=ReviewPriority.MEDIUM,
        category=ReviewCategory.PERFORMANCE,
        context={"threshold": "3.0s", "current_time": "5.2s"},
        tags=["performance-action", "medium-risk"],
        estimated_review_time=8
    )
    print(f"✅ Added performance review: {performance_review}")
    
    # Add a user experience review
    ux_review = queue.add_review_item(
        workflow_id="workflow_003",
        step_number=2,
        action_type="click_button",
        action_data={"button_text": "Submit", "button_id": "submit-btn"},
        reason="Button click confidence below threshold",
        priority=ReviewPriority.LOW,
        category=ReviewCategory.USER_EXPERIENCE,
        context={"confidence": 0.4, "button_visible": True},
        tags=["click-action", "low-confidence", "medium-risk"],
        estimated_review_time=5
    )
    print(f"✅ Added UX review: {ux_review}")
    
    # Test 2: Display queue statistics
    print("\n📊 Test 2: Queue Statistics")
    print("-" * 50)
    stats = queue.get_queue_stats()
    print(f"Total Items: {stats['total_items']}")
    print(f"Pending: {stats['pending']}")
    print(f"By Priority: {stats['by_priority']}")
    print(f"By Category: {stats['by_category']}")
    print(f"Overdue: {stats['overdue_count']}")
    
    # Test 3: Filter reviews
    print("\n🎯 Test 3: Filtering Reviews")
    print("-" * 50)
    
    # Filter by priority
    high_priority = queue.filter_reviews(priority=ReviewPriority.HIGH)
    print(f"High Priority Reviews: {len(high_priority)}")
    for item in high_priority:
        print(f"  - {item.id}: {item.reason}")
    
    # Filter by category
    security_reviews = queue.filter_reviews(category=ReviewCategory.SECURITY)
    print(f"Security Reviews: {len(security_reviews)}")
    for item in security_reviews:
        print(f"  - {item.id}: {item.reason}")
    
    # Test 4: Search functionality
    print("\n🔎 Test 4: Search Functionality")
    print("-" * 50)
    
    search_results = queue.search_reviews("login")
    print(f"Search results for 'login': {len(search_results)}")
    for item in search_results:
        print(f"  - {item.id}: {item.reason}")
    
    # Test 5: Batch operations
    print("\n📦 Test 5: Batch Operations")
    print("-" * 50)
    
    # Get pending reviews
    pending = queue.get_pending_reviews()
    if len(pending) >= 2:
        # Batch approve first two items
        review_ids = [pending[0].id, pending[1].id]
        results = queue.batch_approve(review_ids, "test_reviewer", "Batch approved for testing")
        print(f"Batch approval results: {results}")
    
    # Test 6: Review history
    print("\n📚 Test 6: Review History")
    print("-" * 50)
    
    for item in queue.queue:
        history = queue.get_review_history(item.id)
        print(f"History for {item.id}: {len(history)} entries")
        for entry in history:
            print(f"  - {entry.timestamp}: {entry.action} by {entry.reviewer_id}")
    
    # Test 7: Export functionality
    print("\n💾 Test 7: Export Functionality")
    print("-" * 50)
    
    export_file = "logs/test_review_export.json"
    success = queue.export_review_data(export_file)
    if success:
        print(f"✅ Data exported to: {export_file}")
    else:
        print("❌ Export failed")
    
    print("\n🎉 Enhanced Review Queue Testing Complete!")
    print("=" * 50)
    
    return queue

def main():
    """Main function to run tests and optionally start console"""
    print("🚀 Enhanced Review Queue Test Suite")
    print("=" * 60)
    
    # Run the tests
    queue = test_enhanced_review_queue()
    
    # Ask if user wants to try the interactive console
    print("\n" + "=" * 60)
    print("🎮 INTERACTIVE CONSOLE DEMO")
    print("=" * 60)
    print("Would you like to try the interactive review console?")
    print("This will open a menu-driven interface to manage reviews.")
    
    try:
        choice = input("\nEnter 'y' to start console, or any other key to exit: ").strip().lower()
        if choice == 'y':
            print("\n🎯 Starting Interactive Review Console...")
            print("Use Ctrl+C to exit the console at any time.")
            run_review_console()
        else:
            print("\n👋 Goodbye!")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

if __name__ == "__main__":
    main()
