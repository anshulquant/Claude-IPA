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
                                    <button class="btn btn-primary btn-sm" onclick="reviewManager.approveReview('${review.id}')">
                                        <i class="fas fa-check"></i> Approve
                                    </button>
                                    <button class="btn btn-destructive btn-sm" onclick="reviewManager.rejectReview('${review.id}')">
                                        <i class="fas fa-times"></i> Reject
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
}

// Initialize the review queue manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.reviewManager = new ReviewQueueManager();
});
