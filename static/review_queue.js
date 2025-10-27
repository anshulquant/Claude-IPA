// Review Queue Manager
class ReviewQueueManager {
    constructor() {
        this.selectedReviews = new Set();
        this.currentFilters = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadReviewStats();
        this.loadReviews();
    }

    setupEventListeners() {
        // Review actions
        document.getElementById('refresh-reviews-btn')?.addEventListener('click', () => this.loadReviews());
        document.getElementById('export-reviews-btn')?.addEventListener('click', () => this.exportReviews());
        document.getElementById('search-btn')?.addEventListener('click', () => this.searchReviews());
        document.getElementById('clear-filters-btn')?.addEventListener('click', () => this.clearFilters());
        
        // Batch actions
        document.getElementById('select-all-btn')?.addEventListener('click', () => this.toggleSelectAll());
        document.getElementById('batch-approve-btn')?.addEventListener('click', () => this.batchApprove());
        document.getElementById('batch-reject-btn')?.addEventListener('click', () => this.batchReject());

        // Filter changes
        ['status-filter', 'priority-filter', 'category-filter'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', () => this.applyFilters());
        });

        // Search on enter
        document.getElementById('search-reviews')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchReviews();
        });
    }

    async loadReviewStats() {
        try {
            const response = await fetch('/api/review-queue/stats');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                document.getElementById('total-reviews').textContent = stats.total_items || 0;
                document.getElementById('pending-reviews').textContent = stats.pending || 0;
                document.getElementById('approved-reviews').textContent = stats.approved || 0;
                document.getElementById('overdue-reviews').textContent = stats.overdue_count || 0;
            }
        } catch (error) {
            console.error('Error loading review stats:', error);
        }
    }

    async loadReviews() {
        try {
            const response = await fetch('/api/review-queue/pending');
            const data = await response.json();
            
            if (data.success) {
                this.displayReviews(data.pending_reviews || []);
            }
        } catch (error) {
            console.error('Error loading reviews:', error);
        }
    }

    displayReviews(reviews) {
        const container = document.getElementById('reviews-container');
        
        if (reviews.length === 0) {
            container.innerHTML = '<div class="text-center text-muted-foreground">No reviews found</div>';
            return;
        }

        container.innerHTML = reviews.map(review => `
            <div class="card mb-2" data-review-id="${review.id}">
                <div class="card-content">
                    <div class="flex items-start space-x-4">
                        <div class="checkbox">
                            <input type="checkbox" class="checkbox-input" data-review-id="${review.id}">
                        </div>
                        <div class="flex-1">
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <h4 class="font-semibold mb-1">${review.reason}</h4>
                                    <p class="text-sm text-muted-foreground">Workflow: ${review.workflow_id} | Step: ${review.step_number}</p>
                                    <p class="text-sm text-muted-foreground">Action: ${review.action_type}</p>
                                </div>
                                <div class="flex flex-col space-y-1 text-right">
                                    <div class="badge ${this.getPriorityBadgeClass(review.priority)}">${review.priority}</div>
                                    <div class="badge badge-outline">${review.category || 'other'}</div>
                                    <div class="badge ${this.getStatusBadgeClass(review.status)}">${review.status}</div>
                                </div>
                            </div>
                            <div class="flex justify-between items-center">
                                <small class="text-muted-foreground">Created: ${new Date(review.created_at).toLocaleString()}</small>
                                <div class="flex space-x-2">
                                    <button class="btn btn-primary btn-sm" onclick="reviewManager.openReviewModal('${review.id}')">
                                        <i class="fas fa-eye"></i> Review
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Add checkbox event listeners
        container.querySelectorAll('.checkbox-input').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const reviewId = e.target.dataset.reviewId;
                if (e.target.checked) {
                    this.selectedReviews.add(reviewId);
                } else {
                    this.selectedReviews.delete(reviewId);
                }
                this.updateBatchButtons();
            });
        });
    }

    getPriorityBadgeClass(priority) {
        switch(priority) {
            case 'urgent': return 'badge-destructive';
            case 'high': return 'badge-secondary';
            case 'medium': return 'badge-default';
            case 'low': return 'badge-outline';
            default: return 'badge-outline';
        }
    }

    getStatusBadgeClass(status) {
        switch(status) {
            case 'approved': return 'badge-default';
            case 'rejected': return 'badge-destructive';
            case 'in_review': return 'badge-secondary';
            case 'pending': return 'badge-outline';
            default: return 'badge-outline';
        }
    }

    async searchReviews() {
        const query = document.getElementById('search-reviews').value;
        if (!query.trim()) {
            this.loadReviews();
            return;
        }

        try {
            const response = await fetch(`/api/review-queue/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayReviews(data.reviews || []);
            }
        } catch (error) {
            console.error('Error searching reviews:', error);
        }
    }

    async applyFilters() {
        const status = document.getElementById('status-filter').value;
        const priority = document.getElementById('priority-filter').value;
        const category = document.getElementById('category-filter').value;
        
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        if (category) params.append('category', category);

        try {
            const response = await fetch(`/api/review-queue/filter?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayReviews(data.reviews || []);
            }
        } catch (error) {
            console.error('Error filtering reviews:', error);
        }
    }

    clearFilters() {
        document.getElementById('status-filter').value = '';
        document.getElementById('priority-filter').value = '';
        document.getElementById('category-filter').value = '';
        document.getElementById('search-reviews').value = '';
        this.loadReviews();
    }

    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.checkbox-input');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = !allChecked;
            const reviewId = checkbox.dataset.reviewId;
            if (!allChecked) {
                this.selectedReviews.add(reviewId);
            } else {
                this.selectedReviews.delete(reviewId);
            }
        });
        
        this.updateBatchButtons();
    }

    updateBatchButtons() {
        const hasSelection = this.selectedReviews.size > 0;
        document.getElementById('batch-approve-btn').disabled = !hasSelection;
        document.getElementById('batch-reject-btn').disabled = !hasSelection;
    }

    async batchApprove() {
        if (this.selectedReviews.size === 0) return;
        
        const reviewerId = prompt('Enter your reviewer ID:') || 'web_user';
        const notes = prompt('Enter approval notes (optional):') || '';
        
        try {
            const response = await fetch('/api/review-queue/batch-approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    review_ids: Array.from(this.selectedReviews),
                    reviewer_id: reviewerId,
                    notes: notes
                })
            });
            
            const data = await response.json();
            if (data.success) {
                alert(`Approved ${data.message}`);
                this.selectedReviews.clear();
                this.loadReviews();
                this.loadReviewStats();
            }
        } catch (error) {
            console.error('Error batch approving:', error);
        }
    }

    async batchReject() {
        if (this.selectedReviews.size === 0) return;
        
        const reviewerId = prompt('Enter your reviewer ID:') || 'web_user';
        const notes = prompt('Enter rejection notes (optional):') || '';
        
        try {
            const response = await fetch('/api/review-queue/batch-reject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    review_ids: Array.from(this.selectedReviews),
                    reviewer_id: reviewerId,
                    notes: notes
                })
            });
            
            const data = await response.json();
            if (data.success) {
                alert(`Rejected ${data.message}`);
                this.selectedReviews.clear();
                this.loadReviews();
                this.loadReviewStats();
            }
        } catch (error) {
            console.error('Error batch rejecting:', error);
        }
    }

    async approveReview(reviewId) {
        const reviewerId = prompt('Enter your reviewer ID:') || 'web_user';
        const notes = prompt('Enter approval notes (optional):') || '';
        
        try {
            const response = await fetch(`/api/review-queue/${reviewId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    decision: true,
                    reviewer_id: reviewerId,
                    notes: notes
                })
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Review approved successfully!');
                this.loadReviews();
                this.loadReviewStats();
            }
        } catch (error) {
            console.error('Error approving review:', error);
        }
    }

    async rejectReview(reviewId) {
        const reviewerId = prompt('Enter your reviewer ID:') || 'web_user';
        const notes = prompt('Enter rejection notes (optional):') || '';
        
        try {
            const response = await fetch(`/api/review-queue/${reviewId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    decision: false,
                    reviewer_id: reviewerId,
                    notes: notes
                })
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Review rejected successfully!');
                this.loadReviews();
                this.loadReviewStats();
            }
        } catch (error) {
            console.error('Error rejecting review:', error);
        }
    }

    async exportReviews() {
        try {
            const response = await fetch('/api/review-queue/export', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                alert(`Data exported to: ${data.filepath}`);
            } else {
                alert('Export failed');
            }
        } catch (error) {
            console.error('Error exporting reviews:', error);
        }
    }

    // Modal Functions
    currentReviewId = null;
    currentReviewData = null;

    openReviewModal(reviewId) {
        this.currentReviewId = reviewId;
        
        // Load review details
        this.loadReviewDetails(reviewId);
        
        // Show modal
        const modal = document.getElementById('review-modal');
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    closeReviewModal() {
        const modal = document.getElementById('review-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = '';
        
        // Clean up
        this.currentReviewId = null;
        this.currentReviewData = null;
        this.removeKeyboardShortcuts();
    }

    setupKeyboardShortcuts() {
        this.keyboardHandler = (e) => {
            // Only handle if modal is open
            const modal = document.getElementById('review-modal');
            if (modal.classList.contains('hidden')) return;
            
            // Don't handle if typing in input/textarea
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            if (e.key === 'a' || e.key === 'A') {
                e.preventDefault();
                this.submitReviewDecision(true);
            } else if (e.key === 'r' || e.key === 'R') {
                e.preventDefault();
                this.submitReviewDecision(false);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.closeReviewModal();
            }
        };
        
        document.addEventListener('keydown', this.keyboardHandler);
    }

    removeKeyboardShortcuts() {
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
        }
    }

    async loadReviewDetails(reviewId) {
        try {
            const response = await fetch(`/api/review-queue/${reviewId}`);
            const data = await response.json();
            
            if (data.success && data.review_item) {
                this.currentReviewData = data.review_item;
                this.populateModal(data.review_item);
            }
        } catch (error) {
            console.error('Error loading review details:', error);
        }
    }

    populateModal(review) {
        // Set modal fields
        document.getElementById('modal-action-type').textContent = review.action_type || 'N/A';
        document.getElementById('modal-action-target').textContent = review.action_data?.target || review.target || 'N/A';
        document.getElementById('modal-reason').textContent = review.reason || 'N/A';
        document.getElementById('modal-priority').textContent = review.priority || 'N/A';
        document.getElementById('modal-workflow-id').textContent = review.workflow_id || 'N/A';
        document.getElementById('modal-step-number').textContent = review.step_number || 'N/A';
        
        // Load screenshot if available
        if (review.action_data?.screenshot_path) {
            this.loadScreenshot(review.action_data.screenshot_path);
        } else {
            // Hide loading text
            document.getElementById('screenshot-loading').textContent = 'No screenshot available';
        }
    }

    loadScreenshot(screenshotPath) {
        const img = document.getElementById('review-screenshot');
        const loading = document.getElementById('screenshot-loading');
        
        img.onload = () => {
            loading.textContent = '';
            img.style.display = 'block';
        };
        
        img.onerror = () => {
            loading.textContent = 'Screenshot not found';
            img.style.display = 'none';
        };
        
        img.src = screenshotPath;
    }

    async submitReviewDecision(approved) {
        if (!this.currentReviewId) return;
        
        const reviewerId = document.getElementById('reviewer-id').value || 'web_user';
        const notes = document.getElementById('review-notes').value || '';
        
        try {
            const response = await fetch(`/api/review-queue/${this.currentReviewId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    decision: approved,
                    reviewer_id: reviewerId,
                    notes: notes
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.closeReviewModal();
                this.loadReviews();
                this.loadReviewStats();
                
                // Show success message
                const message = approved ? '✅ Review approved successfully!' : '❌ Review rejected successfully!';
                alert(message);
            } else {
                alert('Failed to submit review');
            }
        } catch (error) {
            console.error('Error submitting review decision:', error);
            alert('Error submitting review');
        }
    }
}

// Initialize the review queue manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.reviewManager = new ReviewQueueManager();
});
