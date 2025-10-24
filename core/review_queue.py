"""
Human Review Queue for Quantanite IPA MVP

This module handles the human review workflow when Claude encounters
situations that require human intervention or approval.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ReviewStatus(Enum):
    """Status of a review item"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ReviewPriority(Enum):
    """Priority level for review items"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ReviewCategory(Enum):
    """Category of review items"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    ACCURACY = "accuracy"
    COMPLIANCE = "compliance"
    USER_EXPERIENCE = "user_experience"
    DATA_QUALITY = "data_quality"
    SYSTEM_STABILITY = "system_stability"
    OTHER = "other"

@dataclass
class ReviewHistory:
    """Represents a single entry in review history"""
    timestamp: datetime
    action: str
    reviewer_id: Optional[str]
    notes: Optional[str]
    status_before: ReviewStatus
    status_after: ReviewStatus

@dataclass
class ReviewItem:
    """Represents a single item in the review queue"""
    id: str
    workflow_id: str
    step_number: int
    action_type: str
    action_data: Dict[str, Any]
    reason: str
    priority: ReviewPriority = ReviewPriority.MEDIUM
    category: ReviewCategory = ReviewCategory.OTHER
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    reviewer_notes: Optional[str] = None
    review_deadline: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[ReviewHistory] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_review_time: Optional[int] = None  # in minutes

class ReviewQueue:
    """
    Manages the human review queue for workflow execution.
    
    This class handles:
    - Adding items to the review queue
    - Assigning reviewers
    - Tracking review status
    - Managing review deadlines
    - Processing review decisions
    - Batch operations
    - Advanced filtering and search
    - Review history tracking
    - Interactive console interface
    """
    
    def __init__(self):
        self.queue: List[ReviewItem] = []
        self.reviewers: Dict[str, Dict[str, Any]] = {}
        self.max_queue_size = 100
        self.default_review_timeout = 3600  # 1 hour in seconds
        self.history_file = "logs/review_history.json"
        self._ensure_logs_directory()
    
    def _ensure_logs_directory(self):
        """Ensure logs directory exists"""
        os.makedirs("logs", exist_ok=True)
    
    def _add_to_history(self, review_item: ReviewItem, action: str, reviewer_id: Optional[str] = None, notes: Optional[str] = None):
        """Add entry to review history"""
        history_entry = ReviewHistory(
            timestamp=datetime.now(),
            action=action,
            reviewer_id=reviewer_id,
            notes=notes,
            status_before=review_item.status,
            status_after=review_item.status
        )
        review_item.history.append(history_entry)
        
    def add_review_item(
        self,
        workflow_id: str,
        step_number: int,
        action_type: str,
        action_data: Dict[str, Any],
        reason: str,
        priority: ReviewPriority = ReviewPriority.MEDIUM,
        category: ReviewCategory = ReviewCategory.OTHER,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        estimated_review_time: Optional[int] = None
    ) -> str:
        """
        Add a new item to the review queue.
        
        Args:
            workflow_id: ID of the workflow requiring review
            step_number: Step number in the workflow
            action_type: Type of action requiring review
            action_data: Data for the action
            reason: Reason why review is needed
            priority: Priority level for the review
            category: Category of the review
            context: Additional context information
            tags: List of tags for the review
            estimated_review_time: Estimated time in minutes
            
        Returns:
            Review item ID
        """
        review_id = f"review_{workflow_id}_{step_number}_{int(datetime.now().timestamp())}"
        
        review_item = ReviewItem(
            id=review_id,
            workflow_id=workflow_id,
            step_number=step_number,
            action_type=action_type,
            action_data=action_data,
            reason=reason,
            priority=priority,
            category=category,
            context=context or {},
            tags=tags or [],
            estimated_review_time=estimated_review_time
        )
        
        # Set review deadline based on priority
        if priority == ReviewPriority.URGENT:
            review_item.review_deadline = datetime.now() + timedelta(hours=2)
        elif priority == ReviewPriority.HIGH:
            review_item.review_deadline = datetime.now() + timedelta(hours=8)
        elif priority == ReviewPriority.MEDIUM:
            review_item.review_deadline = datetime.now() + timedelta(days=1)
        else:  # LOW
            review_item.review_deadline = datetime.now() + timedelta(days=3)
        
        # Add to history
        self._add_to_history(review_item, "created")
        
        self.queue.append(review_item)
        
        # Sort queue by priority and creation time
        self.queue.sort(key=lambda x: (x.priority.value, x.created_at))
        
        logger.info(f"Added review item {review_id} to queue: {reason} (Priority: {priority.value}, Category: {category.value})")
        
        return review_id
    
    def get_pending_reviews(self, reviewer_id: Optional[str] = None) -> List[ReviewItem]:
        """
        Get all pending review items.
        
        Args:
            reviewer_id: Optional reviewer ID to filter by
            
        Returns:
            List of pending review items
        """
        if reviewer_id:
            return [item for item in self.queue if item.status == ReviewStatus.PENDING and item.assigned_to == reviewer_id]
        return [item for item in self.queue if item.status == ReviewStatus.PENDING]
    
    def assign_reviewer(self, review_id: str, reviewer_id: str) -> bool:
        """
        Assign a reviewer to a review item.
        
        Args:
            review_id: ID of the review item
            reviewer_id: ID of the reviewer
            
        Returns:
            True if assignment successful, False otherwise
        """
        for item in self.queue:
            if item.id == review_id and item.status == ReviewStatus.PENDING:
                old_status = item.status
                item.assigned_to = reviewer_id
                item.status = ReviewStatus.IN_REVIEW
                item.updated_at = datetime.now()
                
                # Add to history
                self._add_to_history(item, "assigned", reviewer_id)
                item.history[-1].status_before = old_status
                item.history[-1].status_after = ReviewStatus.IN_REVIEW
                
                logger.info(f"Assigned review {review_id} to reviewer {reviewer_id}")
                return True
        return False
    
    def submit_review(
        self,
        review_id: str,
        reviewer_id: str,
        decision: ReviewStatus,
        notes: Optional[str] = None
    ) -> bool:
        """
        Submit a review decision.
        
        Args:
            review_id: ID of the review item
            reviewer_id: ID of the reviewer
            decision: Review decision (approved/rejected)
            notes: Optional reviewer notes
            
        Returns:
            True if submission successful, False otherwise
        """
        for item in self.queue:
            if item.id == review_id and (item.assigned_to == reviewer_id or item.assigned_to is None):
                old_status = item.status
                item.status = decision
                item.reviewer_notes = notes
                item.updated_at = datetime.now()
                
                # Add to history
                self._add_to_history(item, f"review_{decision.value}", reviewer_id, notes)
                if old_status != decision:
                    item.history[-1].status_before = old_status
                    item.history[-1].status_after = decision
                
                logger.info(f"Review {review_id} decision: {decision.value} by {reviewer_id}")
                return True
        return False
    
    def get_review_status(self, review_id: str) -> Optional[ReviewItem]:
        """
        Get the status of a specific review item.
        
        Args:
            review_id: ID of the review item
            
        Returns:
            Review item if found, None otherwise
        """
        for item in self.queue:
            if item.id == review_id:
                return item
        return None
    
    def cleanup_expired_reviews(self) -> int:
        """
        Clean up expired review items.
        
        Returns:
            Number of items cleaned up
        """
        current_time = datetime.now()
        expired_items = []
        
        for item in self.queue:
            if (item.status == ReviewStatus.PENDING and 
                item.review_deadline and 
                current_time > item.review_deadline):
                item.status = ReviewStatus.EXPIRED
                item.updated_at = current_time
                expired_items.append(item)
        
        logger.info(f"Cleaned up {len(expired_items)} expired review items")
        return len(expired_items)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the review queue.
        
        Returns:
            Dictionary with queue statistics
        """
        stats = {
            "total_items": len(self.queue),
            "pending": len([item for item in self.queue if item.status == ReviewStatus.PENDING]),
            "in_review": len([item for item in self.queue if item.status == ReviewStatus.IN_REVIEW]),
            "approved": len([item for item in self.queue if item.status == ReviewStatus.APPROVED]),
            "rejected": len([item for item in self.queue if item.status == ReviewStatus.REJECTED]),
            "expired": len([item for item in self.queue if item.status == ReviewStatus.EXPIRED]),
            "by_priority": {
                priority.value: len([item for item in self.queue if item.priority == priority])
                for priority in ReviewPriority
            },
            "by_category": {
                category.value: len([item for item in self.queue if item.category == category])
                for category in ReviewCategory
            },
            "avg_review_time": self._calculate_avg_review_time(),
            "overdue_count": len([item for item in self.queue if self._is_overdue(item)])
        }
        return stats
    
    def _calculate_avg_review_time(self) -> Optional[float]:
        """Calculate average review time in minutes"""
        completed_reviews = [item for item in self.queue if item.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]]
        if not completed_reviews:
            return None
        
        total_time = 0
        count = 0
        for item in completed_reviews:
            if len(item.history) >= 2:
                created_time = item.history[0].timestamp
                completed_time = item.history[-1].timestamp
                review_time = (completed_time - created_time).total_seconds() / 60
                total_time += review_time
                count += 1
        
        return total_time / count if count > 0 else None
    
    def _is_overdue(self, item: ReviewItem) -> bool:
        """Check if a review item is overdue"""
        if not item.review_deadline:
            return False
        return datetime.now() > item.review_deadline and item.status == ReviewStatus.PENDING
    
    def filter_reviews(
        self,
        status: Optional[ReviewStatus] = None,
        priority: Optional[ReviewPriority] = None,
        category: Optional[ReviewCategory] = None,
        reviewer_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        overdue_only: bool = False
    ) -> List[ReviewItem]:
        """
        Filter reviews based on various criteria.
        
        Args:
            status: Filter by review status
            priority: Filter by priority level
            category: Filter by category
            reviewer_id: Filter by assigned reviewer
            workflow_id: Filter by workflow ID
            tags: Filter by tags (any match)
            overdue_only: Only return overdue items
            
        Returns:
            List of filtered review items
        """
        filtered = self.queue.copy()
        
        if status:
            filtered = [item for item in filtered if item.status == status]
        
        if priority:
            filtered = [item for item in filtered if item.priority == priority]
        
        if category:
            filtered = [item for item in filtered if item.category == category]
        
        if reviewer_id:
            filtered = [item for item in filtered if item.assigned_to == reviewer_id]
        
        if workflow_id:
            filtered = [item for item in filtered if item.workflow_id == workflow_id]
        
        if tags:
            filtered = [item for item in filtered if any(tag in item.tags for tag in tags)]
        
        if overdue_only:
            filtered = [item for item in filtered if self._is_overdue(item)]
        
        return filtered
    
    def search_reviews(self, query: str) -> List[ReviewItem]:
        """
        Search reviews by text query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching review items
        """
        query_lower = query.lower()
        results = []
        
        for item in self.queue:
            # Search in reason, action_type, reviewer_notes, and tags
            searchable_text = f"{item.reason} {item.action_type} {item.reviewer_notes or ''} {' '.join(item.tags)}"
            if query_lower in searchable_text.lower():
                results.append(item)
        
        return results
    
    def batch_approve(self, review_ids: List[str], reviewer_id: str, notes: Optional[str] = None) -> Dict[str, bool]:
        """
        Approve multiple review items in batch.
        
        Args:
            review_ids: List of review item IDs to approve
            reviewer_id: ID of the reviewer
            notes: Optional notes for all reviews
            
        Returns:
            Dictionary mapping review_id to success status
        """
        results = {}
        for review_id in review_ids:
            success = self.submit_review(review_id, reviewer_id, ReviewStatus.APPROVED, notes)
            results[review_id] = success
        return results
    
    def batch_reject(self, review_ids: List[str], reviewer_id: str, notes: Optional[str] = None) -> Dict[str, bool]:
        """
        Reject multiple review items in batch.
        
        Args:
            review_ids: List of review item IDs to reject
            reviewer_id: ID of the reviewer
            notes: Optional notes for all reviews
            
        Returns:
            Dictionary mapping review_id to success status
        """
        results = {}
        for review_id in review_ids:
            success = self.submit_review(review_id, reviewer_id, ReviewStatus.REJECTED, notes)
            results[review_id] = success
        return results
    
    def get_review_history(self, review_id: str) -> List[ReviewHistory]:
        """
        Get history for a specific review item.
        
        Args:
            review_id: ID of the review item
            
        Returns:
            List of history entries
        """
        item = self.get_review_status(review_id)
        return item.history if item else []
    
    def export_review_data(self, filepath: str) -> bool:
        """
        Export review data to JSON file.
        
        Args:
            filepath: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_items": len(self.queue),
                "reviews": []
            }
            
            for item in self.queue:
                review_data = {
                    "id": item.id,
                    "workflow_id": item.workflow_id,
                    "step_number": item.step_number,
                    "action_type": item.action_type,
                    "reason": item.reason,
                    "priority": item.priority.value,
                    "category": item.category.value,
                    "status": item.status.value,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "assigned_to": item.assigned_to,
                    "reviewer_notes": item.reviewer_notes,
                    "review_deadline": item.review_deadline.isoformat() if item.review_deadline else None,
                    "tags": item.tags,
                    "estimated_review_time": item.estimated_review_time,
                    "history": [
                        {
                            "timestamp": h.timestamp.isoformat(),
                            "action": h.action,
                            "reviewer_id": h.reviewer_id,
                            "notes": h.notes,
                            "status_before": h.status_before.value,
                            "status_after": h.status_after.value
                        }
                        for h in item.history
                    ]
                }
                export_data["reviews"].append(review_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(self.queue)} review items to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export review data: {e}")
            return False

    def interactive_console(self):
        """
        Interactive console interface for managing reviews.
        """
        print("\n" + "="*60)
        print("🔍 QUANTANITE IPA - REVIEW QUEUE MANAGEMENT CONSOLE")
        print("="*60)
        
        while True:
            try:
                self._display_main_menu()
                choice = input("\nEnter your choice (1-9): ").strip()
                
                if choice == "1":
                    self._show_queue_overview()
                elif choice == "2":
                    self._show_pending_reviews()
                elif choice == "3":
                    self._review_single_item()
                elif choice == "4":
                    self._batch_review_items()
                elif choice == "5":
                    self._search_reviews()
                elif choice == "6":
                    self._filter_reviews()
                elif choice == "7":
                    self._show_statistics()
                elif choice == "8":
                    self._export_data()
                elif choice == "9":
                    print("\n👋 Goodbye! Review queue management session ended.")
                    break
                else:
                    print("\n❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Review queue management session ended.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logger.error(f"Console error: {e}")
    
    def _display_main_menu(self):
        """Display the main menu options."""
        print("\n📋 MAIN MENU:")
        print("1. 📊 Queue Overview")
        print("2. ⏳ Pending Reviews")
        print("3. 🔍 Review Single Item")
        print("4. 📦 Batch Review Items")
        print("5. 🔎 Search Reviews")
        print("6. 🎯 Filter Reviews")
        print("7. 📈 Statistics Dashboard")
        print("8. 💾 Export Data")
        print("9. 🚪 Exit")
    
    def _show_queue_overview(self):
        """Show overview of the review queue."""
        stats = self.get_queue_stats()
        
        print("\n📊 QUEUE OVERVIEW")
        print("-" * 40)
        print(f"Total Items: {stats['total_items']}")
        print(f"Pending: {stats['pending']}")
        print(f"In Review: {stats['in_review']}")
        print(f"Approved: {stats['approved']}")
        print(f"Rejected: {stats['rejected']}")
        print(f"Expired: {stats['expired']}")
        print(f"Overdue: {stats['overdue_count']}")
        
        if stats['avg_review_time']:
            print(f"Avg Review Time: {stats['avg_review_time']:.1f} minutes")
        
        print("\n📊 BY PRIORITY:")
        for priority, count in stats['by_priority'].items():
            print(f"  {priority.upper()}: {count}")
        
        print("\n📊 BY CATEGORY:")
        for category, count in stats['by_category'].items():
            print(f"  {category.upper()}: {count}")
    
    def _show_pending_reviews(self):
        """Show all pending reviews."""
        pending = self.get_pending_reviews()
        
        if not pending:
            print("\n✅ No pending reviews!")
            return
        
        print(f"\n⏳ PENDING REVIEWS ({len(pending)})")
        print("-" * 80)
        
        for i, item in enumerate(pending, 1):
            overdue = "🔴 OVERDUE" if self._is_overdue(item) else ""
            print(f"{i:2d}. {item.id}")
            print(f"    Workflow: {item.workflow_id} | Step: {item.step_number}")
            print(f"    Action: {item.action_type} | Priority: {item.priority.value.upper()}")
            print(f"    Category: {item.category.value.upper()} | {overdue}")
            print(f"    Reason: {item.reason}")
            if item.tags:
                print(f"    Tags: {', '.join(item.tags)}")
            print(f"    Created: {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if item.review_deadline:
                print(f"    Deadline: {item.review_deadline.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
    
    def _review_single_item(self):
        """Review a single item."""
        pending = self.get_pending_reviews()
        
        if not pending:
            print("\n✅ No pending reviews!")
            return
        
        self._show_pending_reviews()
        
        try:
            choice = int(input(f"\nSelect item to review (1-{len(pending)}): ")) - 1
            if 0 <= choice < len(pending):
                item = pending[choice]
                self._process_single_review(item)
            else:
                print("❌ Invalid selection!")
        except ValueError:
            print("❌ Please enter a valid number!")
    
    def _process_single_review(self, item: ReviewItem):
        """Process a single review item."""
        print(f"\n🔍 REVIEWING: {item.id}")
        print("-" * 50)
        print(f"Workflow: {item.workflow_id}")
        print(f"Step: {item.step_number}")
        print(f"Action: {item.action_type}")
        print(f"Priority: {item.priority.value.upper()}")
        print(f"Category: {item.category.value.upper()}")
        print(f"Reason: {item.reason}")
        print(f"Created: {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if item.tags:
            print(f"Tags: {', '.join(item.tags)}")
        
        print(f"\nAction Data:")
        for key, value in item.action_data.items():
            print(f"  {key}: {value}")
        
        print(f"\nContext:")
        for key, value in item.context.items():
            print(f"  {key}: {value}")
        
        print("\n📝 REVIEW OPTIONS:")
        print("1. ✅ Approve")
        print("2. ❌ Reject")
        print("3. ⏸️  Skip")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            notes = input("Enter approval notes (optional): ").strip() or None
            reviewer_id = input("Enter your reviewer ID: ").strip() or "console_user"
            
            if self.submit_review(item.id, reviewer_id, ReviewStatus.APPROVED, notes):
                print("✅ Review approved successfully!")
            else:
                print("❌ Failed to approve review!")
                
        elif choice == "2":
            notes = input("Enter rejection notes (optional): ").strip() or None
            reviewer_id = input("Enter your reviewer ID: ").strip() or "console_user"
            
            if self.submit_review(item.id, reviewer_id, ReviewStatus.REJECTED, notes):
                print("❌ Review rejected successfully!")
            else:
                print("❌ Failed to reject review!")
        else:
            print("⏸️  Review skipped.")
    
    def _batch_review_items(self):
        """Batch review multiple items."""
        pending = self.get_pending_reviews()
        
        if not pending:
            print("\n✅ No pending reviews!")
            return
        
        self._show_pending_reviews()
        
        print("\n📦 BATCH REVIEW")
        print("Enter item numbers to review (comma-separated, e.g., 1,3,5):")
        try:
            choices = input("Items: ").strip()
            if not choices:
                print("❌ No items selected!")
                return
            
            indices = [int(x.strip()) - 1 for x in choices.split(",")]
            selected_items = [pending[i] for i in indices if 0 <= i < len(pending)]
            
            if not selected_items:
                print("❌ No valid items selected!")
                return
            
            print(f"\nSelected {len(selected_items)} items for batch review:")
            for item in selected_items:
                print(f"  - {item.id} ({item.priority.value.upper()})")
            
            print("\n📝 BATCH REVIEW OPTIONS:")
            print("1. ✅ Approve All")
            print("2. ❌ Reject All")
            print("3. ⏸️  Cancel")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice in ["1", "2"]:
                reviewer_id = input("Enter your reviewer ID: ").strip() or "console_user"
                notes = input("Enter notes for all reviews (optional): ").strip() or None
                
                review_ids = [item.id for item in selected_items]
                
                if choice == "1":
                    results = self.batch_approve(review_ids, reviewer_id, notes)
                    approved = sum(1 for success in results.values() if success)
                    print(f"✅ Approved {approved}/{len(review_ids)} items successfully!")
                else:
                    results = self.batch_reject(review_ids, reviewer_id, notes)
                    rejected = sum(1 for success in results.values() if success)
                    print(f"❌ Rejected {rejected}/{len(review_ids)} items successfully!")
            else:
                print("⏸️  Batch review cancelled.")
                
        except ValueError:
            print("❌ Invalid input format!")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _search_reviews(self):
        """Search reviews by text query."""
        query = input("\n🔎 Enter search query: ").strip()
        if not query:
            print("❌ Empty search query!")
            return
        
        results = self.search_reviews(query)
        
        if not results:
            print(f"\n❌ No results found for '{query}'")
            return
        
        print(f"\n🔎 SEARCH RESULTS for '{query}' ({len(results)} found)")
        print("-" * 60)
        
        for i, item in enumerate(results, 1):
            print(f"{i:2d}. {item.id} - {item.status.value.upper()}")
            print(f"    {item.reason}")
            print(f"    Priority: {item.priority.value.upper()} | Category: {item.category.value.upper()}")
            print()
    
    def _filter_reviews(self):
        """Filter reviews by criteria."""
        print("\n🎯 FILTER REVIEWS")
        print("1. By Status")
        print("2. By Priority")
        print("3. By Category")
        print("4. By Workflow ID")
        print("5. Overdue Only")
        print("6. ⏸️  Cancel")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        filtered = []
        
        if choice == "1":
            print("\nStatus options:")
            for i, status in enumerate(ReviewStatus, 1):
                print(f"{i}. {status.value.upper()}")
            try:
                status_choice = int(input("Select status: ")) - 1
                if 0 <= status_choice < len(ReviewStatus):
                    status = list(ReviewStatus)[status_choice]
                    filtered = self.filter_reviews(status=status)
            except ValueError:
                print("❌ Invalid choice!")
                return
                
        elif choice == "2":
            print("\nPriority options:")
            for i, priority in enumerate(ReviewPriority, 1):
                print(f"{i}. {priority.value.upper()}")
            try:
                priority_choice = int(input("Select priority: ")) - 1
                if 0 <= priority_choice < len(ReviewPriority):
                    priority = list(ReviewPriority)[priority_choice]
                    filtered = self.filter_reviews(priority=priority)
            except ValueError:
                print("❌ Invalid choice!")
                return
                
        elif choice == "3":
            print("\nCategory options:")
            for i, category in enumerate(ReviewCategory, 1):
                print(f"{i}. {category.value.upper()}")
            try:
                category_choice = int(input("Select category: ")) - 1
                if 0 <= category_choice < len(ReviewCategory):
                    category = list(ReviewCategory)[category_choice]
                    filtered = self.filter_reviews(category=category)
            except ValueError:
                print("❌ Invalid choice!")
                return
                
        elif choice == "4":
            workflow_id = input("Enter workflow ID: ").strip()
            if workflow_id:
                filtered = self.filter_reviews(workflow_id=workflow_id)
            else:
                print("❌ Empty workflow ID!")
                return
                
        elif choice == "5":
            filtered = self.filter_reviews(overdue_only=True)
            
        else:
            print("⏸️  Filter cancelled.")
            return
        
        if not filtered:
            print("\n❌ No items match the filter criteria!")
            return
        
        print(f"\n🎯 FILTERED RESULTS ({len(filtered)} found)")
        print("-" * 60)
        
        for i, item in enumerate(filtered, 1):
            overdue = "🔴 OVERDUE" if self._is_overdue(item) else ""
            print(f"{i:2d}. {item.id} - {item.status.value.upper()}")
            print(f"    {item.reason}")
            print(f"    Priority: {item.priority.value.upper()} | Category: {item.category.value.upper()} | {overdue}")
            print()
    
    def _show_statistics(self):
        """Show detailed statistics."""
        stats = self.get_queue_stats()
        
        print("\n📈 DETAILED STATISTICS")
        print("=" * 50)
        
        print(f"📊 OVERVIEW:")
        print(f"  Total Items: {stats['total_items']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  In Review: {stats['in_review']}")
        print(f"  Approved: {stats['approved']}")
        print(f"  Rejected: {stats['rejected']}")
        print(f"  Expired: {stats['expired']}")
        print(f"  Overdue: {stats['overdue_count']}")
        
        if stats['avg_review_time']:
            print(f"  Average Review Time: {stats['avg_review_time']:.1f} minutes")
        else:
            print(f"  Average Review Time: No completed reviews")
        
        print(f"\n📊 BY PRIORITY:")
        for priority, count in stats['by_priority'].items():
            percentage = (count / stats['total_items'] * 100) if stats['total_items'] > 0 else 0
            print(f"  {priority.upper()}: {count} ({percentage:.1f}%)")
        
        print(f"\n📊 BY CATEGORY:")
        for category, count in stats['by_category'].items():
            percentage = (count / stats['total_items'] * 100) if stats['total_items'] > 0 else 0
            print(f"  {category.upper()}: {count} ({percentage:.1f}%)")
    
    def _export_data(self):
        """Export review data to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"review_export_{timestamp}.json"
        filepath = f"logs/{filename}"
        
        if self.export_review_data(filepath):
            print(f"✅ Data exported successfully to: {filepath}")
        else:
            print("❌ Failed to export data!")

# Global review queue instance
review_queue = ReviewQueue()

def get_review_queue() -> ReviewQueue:
    """Get the global review queue instance."""
    return review_queue

def run_review_console():
    """Run the interactive review console."""
    queue = get_review_queue()
    queue.interactive_console()