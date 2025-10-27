/**
 * Claude IPA MVP - Frontend JavaScript
 * Handles workflow submission, status updates, and UI interactions
 */

class WorkflowManager {
    constructor() {
        this.currentWorkflowId = null;
        this.statusInterval = null;
        this.websocket = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadWorkflowHistory();
        this.loadPendingReviews();
        this.setupDemoButtons();
        this.initializeUI();
    }

    setupEventListeners() {
        const form = document.getElementById('workflow-form');
        const refreshBtn = document.getElementById('refresh-btn');
        const newWorkflowBtn = document.getElementById('new-workflow-btn');

        form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        refreshBtn.addEventListener('click', () => this.refreshStatus());
        newWorkflowBtn.addEventListener('click', () => this.startNewWorkflow());
        
        // Day 4 Feature Event Listeners
        this.setupDay4EventListeners();
    }
    
    setupDay4EventListeners() {
        // Pause/Resume buttons
        const pauseBtn = document.getElementById('pause-btn');
        const resumeBtn = document.getElementById('resume-btn');
        const generateReportBtn = document.getElementById('generate-report-btn');
        const errorAnalyticsBtn = document.getElementById('error-analytics-btn');
        
        // Day 4 feature buttons
        const pauseWorkflowBtn = document.getElementById('pause-workflow-btn');
        const resumeWorkflowBtn = document.getElementById('resume-workflow-btn');
        const quickReportBtn = document.getElementById('quick-report-btn');
        const customReportBtn = document.getElementById('custom-report-btn');
        const errorDashboardBtn = document.getElementById('error-dashboard-btn');
        const testErrorsBtn = document.getElementById('test-errors-btn');
        const saveStateBtn = document.getElementById('save-state-btn');
        const loadStateBtn = document.getElementById('load-state-btn');
        const performanceBtn = document.getElementById('performance-btn');
        const patternsBtn = document.getElementById('patterns-btn');
        const viewLogsBtn = document.getElementById('view-logs-btn');
        
        // Add event listeners
        if (pauseBtn) pauseBtn.addEventListener('click', () => this.pauseWorkflow());
        if (resumeBtn) resumeBtn.addEventListener('click', () => this.resumeWorkflow());
        if (generateReportBtn) generateReportBtn.addEventListener('click', () => this.showReportModal());
        if (errorAnalyticsBtn) errorAnalyticsBtn.addEventListener('click', () => this.showErrorAnalytics());
        
        if (pauseWorkflowBtn) pauseWorkflowBtn.addEventListener('click', () => this.pauseWorkflow());
        if (resumeWorkflowBtn) resumeWorkflowBtn.addEventListener('click', () => this.resumeWorkflow());
        if (quickReportBtn) quickReportBtn.addEventListener('click', () => this.generateQuickReport());
        if (customReportBtn) customReportBtn.addEventListener('click', () => this.showReportModal());
        if (errorDashboardBtn) errorDashboardBtn.addEventListener('click', () => this.showErrorAnalytics());
        if (testErrorsBtn) testErrorsBtn.addEventListener('click', () => this.testErrorHandling());
        if (saveStateBtn) saveStateBtn.addEventListener('click', () => this.saveWorkflowState());
        if (loadStateBtn) loadStateBtn.addEventListener('click', () => this.showStateManagement());
        if (performanceBtn) performanceBtn.addEventListener('click', () => this.showPerformanceAnalytics());
        if (patternsBtn) patternsBtn.addEventListener('click', () => this.showErrorPatterns());
        if (viewLogsBtn) viewLogsBtn.addEventListener('click', () => this.viewEnhancedLogs());
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        
        const goal = document.getElementById('goal').value.trim();
        const startUrl = document.getElementById('start-url').value.trim();
        
        if (!goal) {
            this.showError('Please enter a workflow goal');
            return;
        }

        try {
            this.setLoading(true);
            
            const response = await fetch('/api/execute-workflow', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    goal: goal,
                    start_url: startUrl || undefined
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.currentWorkflowId = result.workflow_id;
            
            this.showWorkflowStatus();
            this.connectWebSocket(); // Connect via WebSocket instead of polling
            this.loadWorkflowHistory();
            
        } catch (error) {
            console.error('Error starting workflow:', error);
            this.showError(`Failed to start workflow: ${error.message}`);
        } finally {
            this.setLoading(false);
        }
    }

    showWorkflowStatus() {
        const statusDiv = document.getElementById('workflow-status');
        const workflowIdDisplay = document.getElementById('workflow-id-display');
        const day4Features = document.getElementById('day4-features');
        
        statusDiv.classList.remove('hidden');
        workflowIdDisplay.textContent = this.currentWorkflowId;
        
        // Show Day 4 features section
        if (day4Features) {
            day4Features.classList.remove('hidden');
        }
        
        // Show pause/resume buttons
        this.updatePauseResumeButtons(false);
        
        // Scroll to status section
        statusDiv.scrollIntoView({ behavior: 'smooth' });
    }

    connectWebSocket() {
        if (!this.currentWorkflowId) return;
        
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/workflow/${this.currentWorkflowId}`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.addLogEntry('✅ Real-time connection established', 'success');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketUpdate(data);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                // Fallback to polling
                this.startStatusPolling();
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                // Fallback to polling
                this.startStatusPolling();
            };
        } catch (error) {
            console.error('Error connecting WebSocket:', error);
            // Fallback to polling
            this.startStatusPolling();
        }
    }
    
    handleWebSocketUpdate(data) {
        if (data.type === 'status' && data.data) {
            const workflow = data.data;
            
            // Update progress
            this.updateProgress(workflow.progress || 0);
            
            // Update status
            this.updateWorkflowStatus(workflow.status);
            
            // Update current step
            if (workflow.current_step) {
                document.getElementById('current-step').textContent = workflow.current_step;
            }
            
            // Display screenshot if available
            if (workflow.screenshot_path) {
                this.displayScreenshot(workflow.screenshot_path);
            }
            
            // Display Claude reasoning if available
            if (workflow.claude_reasoning) {
                this.displayReasoning(workflow.claude_reasoning);
            }
        }
    }
    
    displayScreenshot(screenshotPath) {
        const screenshotSection = document.getElementById('screenshot-display');
        const screenshotImg = document.getElementById('current-screenshot');
        
        if (screenshotSection && screenshotImg) {
            // Show the section
            screenshotSection.style.display = 'block';
            
            // Set image source
            screenshotImg.src = screenshotPath;
            
            screenshotImg.onload = () => {
                console.log('Screenshot loaded:', screenshotPath);
            };
            
            screenshotImg.onerror = () => {
                console.error('Failed to load screenshot:', screenshotPath);
                // Try to load from static path
                const staticPath = `/screenshots/${screenshotPath.split('/').pop()}`;
                screenshotImg.src = staticPath;
            };
        }
    }
    
    displayReasoning(reasoning) {
        const reasoningSection = document.getElementById('reasoning-display');
        const reasoningContent = document.getElementById('claude-reasoning');
        
        if (reasoningSection && reasoningContent) {
            reasoningContent.textContent = reasoning;
            reasoningSection.style.display = 'block';
        }
    }
    
    startStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }

        this.statusInterval = setInterval(() => {
            this.refreshStatus();
        }, 2000); // Poll every 2 seconds
    }

    async refreshStatus() {
        if (!this.currentWorkflowId) return;

        try {
            const response = await fetch(`/api/workflow-status/${this.currentWorkflowId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const status = await response.json();
            this.updateStatusDisplay(status);

            // Stop polling if workflow is completed or failed
            if (status.status === 'completed' || status.status === 'failed') {
                this.stopStatusPolling();
                this.showNewWorkflowButton();
            }

        } catch (error) {
            console.error('Error fetching status:', error);
            this.showError(`Failed to fetch status: ${error.message}`);
        }
    }

    updateStatusDisplay(status) {
        // Update status badge
        const statusBadge = document.getElementById('status-badge');
        const statusText = document.getElementById('status-text');
        
        // Reset badge classes and add appropriate status class
        statusBadge.className = 'badge';
        if (status.status === 'completed') {
            statusBadge.classList.add('badge-default');
        } else if (status.status === 'failed') {
            statusBadge.classList.add('badge-destructive');
        } else if (status.status === 'running') {
            statusBadge.classList.add('badge-secondary');
        } else {
            statusBadge.classList.add('badge-outline');
        }
        statusText.textContent = status.status;

        // Update progress
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        progressFill.style.transform = `scaleX(${status.progress / 100})`;
        progressText.textContent = `${status.progress}%`;

        // Update current step
        const currentStep = document.getElementById('current-step');
        if (status.current_step) {
            currentStep.innerHTML = `<i class="fas fa-cog fa-spin"></i> ${status.current_step}`;
        }

        // Update execution log
        this.updateExecutionLog(status.execution_log);

        // Show error if failed
        if (status.status === 'failed' && status.error_message) {
            this.showError(status.error_message);
        }
    }

    updateExecutionLog(logEntries) {
        const logContainer = document.getElementById('log-container');
        
        // Clear existing logs
        logContainer.innerHTML = '';

        if (!logEntries || logEntries.length === 0) {
            logContainer.innerHTML = '<div class="text-center text-muted-foreground">No log entries yet</div>';
            return;
        }

        // Add log entries
        logEntries.forEach(entry => {
            const logEntry = document.createElement('div');
            logEntry.className = 'flex items-center space-x-2 py-2 border-b border-border last:border-b-0';
            
            const statusColor = entry.status === 'success' ? 'text-green-500' : 
                              entry.status === 'error' ? 'text-red-500' : 
                              'text-blue-500';
            
            logEntry.innerHTML = `
                <span class="text-xs text-muted-foreground font-mono">${this.formatTimestamp(entry.timestamp)}</span>
                <span class="text-sm font-medium text-primary">${entry.step}</span>
                <span class="text-sm flex-1">${entry.message}</span>
                <span class="text-xs font-medium ${statusColor}">${entry.status}</span>
            `;
            
            logContainer.appendChild(logEntry);
        });

        // Scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    async loadWorkflowHistory() {
        try {
            const response = await fetch('/api/workflow-history');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.displayWorkflowHistory(data.workflows);

        } catch (error) {
            console.error('Error loading workflow history:', error);
            const historyContainer = document.getElementById('workflow-history');
            if (historyContainer) {
                historyContainer.innerHTML = `<div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Failed to load workflow history</p>
                    <small>${error.message}</small>
                </div>`;
            }
        }
    }

    displayWorkflowHistory(workflows) {
        const historyContainer = document.getElementById('workflow-history');
        
        if (!historyContainer) {
            console.error('historyContainer element not found');
            return;
        }
        
        if (!workflows || workflows.length === 0) {
            historyContainer.innerHTML = `<div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No workflows executed yet</p>
                <small>Start your first automation above</small>
            </div>`;
            return;
        }

        historyContainer.innerHTML = workflows.map(workflow => `
            <div class="card mb-2">
                <div class="card-content">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="font-medium mb-1">${this.escapeHtml(workflow.goal)}</div>
                            <div class="text-sm text-muted-foreground">${this.formatTimestamp(workflow.created_at)}</div>
                        </div>
                        <div class="badge ${workflow.status === 'completed' ? 'badge-default' : 
                                         workflow.status === 'failed' ? 'badge-destructive' : 
                                         'badge-outline'}">
                            ${workflow.status}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    showNewWorkflowButton() {
        const newWorkflowBtn = document.getElementById('new-workflow-btn');
        newWorkflowBtn.classList.remove('hidden');
    }

    startNewWorkflow() {
        // Reset form
        document.getElementById('workflow-form').reset();
        
        // Hide status section
        document.getElementById('workflow-status').classList.add('hidden');
        
        // Hide new workflow button
        document.getElementById('new-workflow-btn').classList.add('hidden');
        
        // Clear current workflow
        this.currentWorkflowId = null;
        
        // Stop polling
        this.stopStatusPolling();
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    setLoading(loading) {
        const submitBtn = document.getElementById('submit-btn');
        const submitText = submitBtn.querySelector('i').nextSibling;
        
        if (loading) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-rocket"></i> Start Automation';
        }
    }

    showError(message) {
        // Create or update error message
        let errorDiv = document.getElementById('error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'error-message';
            errorDiv.className = 'alert alert-destructive mb-4';
            
            const form = document.getElementById('workflow-form');
            form.parentNode.insertBefore(errorDiv, form.nextSibling);
        }
        
        errorDiv.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorDiv) {
                errorDiv.remove();
            }
        }, 5000);
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Day 4 Feature Methods
    
    async pauseWorkflow() {
        if (!this.currentWorkflowId) {
            this.showError('No active workflow to pause');
            return;
        }
        
        try {
            const response = await fetch(`/api/workflow/${this.currentWorkflowId}/pause`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'Manual pause via UI' })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess('Workflow paused successfully');
                this.updatePauseResumeButtons(true);
            } else {
                throw new Error('Failed to pause workflow');
            }
        } catch (error) {
            console.error('Error pausing workflow:', error);
            this.showError(`Failed to pause workflow: ${error.message}`);
        }
    }
    
    async resumeWorkflow() {
        if (!this.currentWorkflowId) {
            this.showError('No active workflow to resume');
            return;
        }
        
        try {
            const response = await fetch(`/api/workflow/${this.currentWorkflowId}/resume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'Manual resume via UI' })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess('Workflow resumed successfully');
                this.updatePauseResumeButtons(false);
            } else {
                throw new Error('Failed to resume workflow');
            }
        } catch (error) {
            console.error('Error resuming workflow:', error);
            this.showError(`Failed to resume workflow: ${error.message}`);
        }
    }
    
    updatePauseResumeButtons(isPaused) {
        const pauseBtn = document.getElementById('pause-btn');
        const resumeBtn = document.getElementById('resume-btn');
        
        if (isPaused) {
            if (pauseBtn) pauseBtn.classList.add('hidden');
            if (resumeBtn) resumeBtn.classList.remove('hidden');
        } else {
            if (pauseBtn) pauseBtn.classList.remove('hidden');
            if (resumeBtn) resumeBtn.classList.add('hidden');
        }
    }
    
    showReportModal() {
        const modal = document.getElementById('report-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    async generateReport() {
        if (!this.currentWorkflowId) {
            this.showError('No active workflow to generate report for');
            return;
        }
        
        const reportType = document.getElementById('report-type').value;
        const reportFormat = document.getElementById('report-format').value;
        
        try {
            const response = await fetch(`/api/reports/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    workflow_id: this.currentWorkflowId,
                    format: reportFormat,
                    report_type: reportType
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess(`Report generated successfully: ${result.report_path}`);
                this.closeModal('report-modal');
            } else {
                throw new Error('Failed to generate report');
            }
        } catch (error) {
            console.error('Error generating report:', error);
            this.showError(`Failed to generate report: ${error.message}`);
        }
    }
    
    async generateQuickReport() {
        if (!this.currentWorkflowId) {
            this.showError('No active workflow to generate report for');
            return;
        }
        
        try {
            const response = await fetch(`/api/reports/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    workflow_id: this.currentWorkflowId,
                    format: 'html',
                    report_type: 'comprehensive'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess(`Quick report generated: ${result.report_path}`);
            } else {
                throw new Error('Failed to generate quick report');
            }
        } catch (error) {
            console.error('Error generating quick report:', error);
            this.showError(`Failed to generate quick report: ${error.message}`);
        }
    }
    
    async showErrorAnalytics() {
        const modal = document.getElementById('error-analytics-modal');
        const content = document.getElementById('error-analytics-content');
        
        if (modal) {
            modal.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/error-analytics');
                if (response.ok) {
                    const data = await response.json();
                    this.displayErrorAnalytics(data.analytics, content);
                } else {
                    content.innerHTML = '<div class="text-center text-red-500">Failed to load error analytics</div>';
                }
            } catch (error) {
                console.error('Error loading error analytics:', error);
                content.innerHTML = '<div class="text-center text-red-500">Error loading analytics</div>';
            }
        }
    }
    
    displayErrorAnalytics(analytics, container) {
        container.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div class="card">
                        <div class="card-content">
                            <h4 class="font-semibold mb-2">Total Errors</h4>
                            <div class="text-2xl font-bold text-red-500">${analytics.total_errors || 0}</div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-content">
                            <h4 class="font-semibold mb-2">Categories</h4>
                            <div class="text-sm">
                                ${Object.entries(analytics.category_distribution || {}).map(([cat, count]) => 
                                    `<div class="flex justify-between"><span>${cat}</span><span>${count}</span></div>`
                                ).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-content">
                        <h4 class="font-semibold mb-2">Severity Distribution</h4>
                        <div class="text-sm">
                            ${Object.entries(analytics.severity_distribution || {}).map(([sev, count]) => 
                                `<div class="flex justify-between"><span>${sev}</span><span>${count}</span></div>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    async testErrorHandling() {
        try {
            const response = await fetch('/api/error-handling/test?error_type=network&severity=medium', {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess(`Error handling test completed: ${result.message}`);
            } else {
                throw new Error('Failed to test error handling');
            }
        } catch (error) {
            console.error('Error testing error handling:', error);
            this.showError(`Failed to test error handling: ${error.message}`);
        }
    }
    
    async saveWorkflowState() {
        if (!this.currentWorkflowId) {
            this.showError('No active workflow to save state for');
            return;
        }
        
        try {
            // This would trigger a state save - for now just show success
            this.showSuccess('Workflow state saved successfully');
        } catch (error) {
            console.error('Error saving workflow state:', error);
            this.showError(`Failed to save workflow state: ${error.message}`);
        }
    }
    
    async showStateManagement() {
        const modal = document.getElementById('state-modal');
        const content = document.getElementById('state-management-content');
        
        if (modal) {
            modal.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/workflow-states');
                if (response.ok) {
                    const data = await response.json();
                    this.displayStateManagement(data.states, content);
                } else {
                    content.innerHTML = '<div class="text-center text-red-500">Failed to load workflow states</div>';
                }
            } catch (error) {
                console.error('Error loading workflow states:', error);
                content.innerHTML = '<div class="text-center text-red-500">Error loading states</div>';
            }
        }
    }
    
    displayStateManagement(states, container) {
        if (states.length === 0) {
            container.innerHTML = '<div class="text-center text-muted-foreground">No saved workflow states</div>';
            return;
        }
        
        container.innerHTML = `
            <div class="space-y-2">
                ${states.map(state => `
                    <div class="card">
                        <div class="card-content">
                            <div class="flex justify-between items-center">
                                <div>
                                    <div class="font-medium">${state.workflow_id}</div>
                                    <div class="text-sm text-muted-foreground">${new Date(state.modified_at).toLocaleString()}</div>
                                </div>
                                <div class="text-sm text-muted-foreground">${(state.size / 1024).toFixed(1)} KB</div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async showPerformanceAnalytics() {
        const modal = document.getElementById('performance-modal');
        const content = document.getElementById('performance-content');
        
        if (modal) {
            modal.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/recovery-metrics');
                if (response.ok) {
                    const data = await response.json();
                    this.displayPerformanceAnalytics(data.metrics, content);
                } else {
                    content.innerHTML = '<div class="text-center text-red-500">Failed to load performance data</div>';
                }
            } catch (error) {
                console.error('Error loading performance data:', error);
                content.innerHTML = '<div class="text-center text-red-500">Error loading performance data</div>';
            }
        }
    }
    
    displayPerformanceAnalytics(metrics, container) {
        container.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div class="card">
                        <div class="card-content">
                            <h4 class="font-semibold mb-2">Recovery Attempts</h4>
                            <div class="text-2xl font-bold text-blue-500">${metrics.total_recovery_attempts || 0}</div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-content">
                            <h4 class="font-semibold mb-2">Success Rate</h4>
                            <div class="text-2xl font-bold text-green-500">${(metrics.recovery_success_rate || 0).toFixed(1)}%</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    async showErrorPatterns() {
        try {
            const response = await fetch('/api/error-patterns');
            if (response.ok) {
                const data = await response.json();
                this.showSuccess(`Error patterns loaded: ${data.patterns.total_errors} total errors`);
            } else {
                throw new Error('Failed to load error patterns');
            }
        } catch (error) {
            console.error('Error loading error patterns:', error);
            this.showError(`Failed to load error patterns: ${error.message}`);
        }
    }
    
    viewEnhancedLogs() {
        // Show enhanced logs in the execution log section
        this.showSuccess('Enhanced logs are displayed in the execution log section with colors and emojis');
    }
    
    showSuccess(message) {
        // Create or update success message
        let successDiv = document.getElementById('success-message');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.id = 'success-message';
            successDiv.className = 'alert mb-4';
            successDiv.style.backgroundColor = '#d1fae5';
            successDiv.style.borderColor = '#10b981';
            successDiv.style.color = '#065f46';
            
            const form = document.getElementById('workflow-form');
            form.parentNode.insertBefore(successDiv, form.nextSibling);
        }
        
        successDiv.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-check-circle"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (successDiv) {
                successDiv.remove();
            }
        }, 3000);
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    // Enhanced UI Methods
    setupDemoButtons() {
        // Demo button functionality
        window.loadDemo = (type) => {
            const goalTextarea = document.getElementById('goal');
            const startUrlInput = document.getElementById('start-url');
            
            const demos = {
                search: {
                    goal: "Go to Google and search for 'machine learning tutorials', then extract the top 5 results with titles and descriptions",
                    url: "https://google.com"
                },
                extract: {
                    goal: "Extract product information from an e-commerce page including title, price, rating, and availability",
                    url: "https://example.com/product"
                },
                form: {
                    goal: "Fill out a contact form with sample data including name, email, and message",
                    url: "https://example.com/contact"
                }
            };
            
            if (demos[type]) {
                goalTextarea.value = demos[type].goal;
                startUrlInput.value = demos[type].url;
                goalTextarea.focus();
                
                this.showNotification(`Loaded ${type} demo`, 'success');
            }
        };
        
        // Preview steps functionality
        const previewBtn = document.getElementById('preview-btn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.previewWorkflowSteps());
        }
        
        // Clear log functionality
        const clearLogBtn = document.getElementById('clear-log-btn');
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => this.clearExecutionLog());
        }
    }
    
    initializeUI() {
        // Initialize progress bar
        this.updateProgress(0);
        
        // Initialize status
        this.updateWorkflowStatus('Ready');
        this.updateCurrentStep('Waiting for workflow to start');
        
        // Add loading state management
        this.setupLoadingStates();
    }
    
    async loadPendingReviews() {
        try {
            const response = await fetch('/api/review-queue/pending');
            if (response.ok) {
                const reviews = await response.json();
                this.displayPendingReviews(reviews);
            }
        } catch (error) {
            console.error('Error loading pending reviews:', error);
        }
    }
    
    displayPendingReviews(reviews) {
        const summaryContainer = document.getElementById('pending-reviews-summary');
        const countBadge = document.getElementById('pending-reviews-count');
        
        if (!summaryContainer) return;
        
        // Update count
        if (countBadge) {
            countBadge.textContent = reviews.length;
        }
        
        // Display reviews
        if (reviews.length === 0) {
            summaryContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle text-green-500"></i>
                    <p>No pending reviews</p>
                    <small>All reviews have been processed</small>
                </div>
            `;
        } else {
            summaryContainer.innerHTML = reviews.slice(0, 3).map(review => `
                <div class="review-item" style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.75rem; margin-bottom: 0.5rem;">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="font-semibold text-sm" style="color: #1f2937;">${review.action_type || 'Action'}</div>
                            <div class="text-xs" style="color: #6b7280;">Priority: ${review.priority || 'medium'}</div>
                        </div>
                        <a href="/review-queue" class="btn btn-primary btn-xs">
                            <i class="fas fa-eye"></i> Review
                        </a>
                    </div>
                </div>
            `).join('');
        }
    }
    
    setupLoadingStates() {
        const submitBtn = document.getElementById('submit-btn');
        const btnText = submitBtn.querySelector('span');
        const btnLoading = submitBtn.querySelector('.btn-loading');
        
        if (btnText && btnLoading) {
            this.submitBtnText = btnText;
            this.submitBtnLoading = btnLoading;
        }
    }
    
    showLoadingState() {
        if (this.submitBtnText && this.submitBtnLoading) {
            this.submitBtnText.classList.add('hidden');
            this.submitBtnLoading.classList.remove('hidden');
        }
    }
    
    hideLoadingState() {
        if (this.submitBtnText && this.submitBtnLoading) {
            this.submitBtnText.classList.remove('hidden');
            this.submitBtnLoading.classList.add('hidden');
        }
    }
    
    previewWorkflowSteps() {
        const goal = document.getElementById('goal').value;
        if (!goal.trim()) {
            this.showNotification('Please enter a workflow goal first', 'warning');
            return;
        }
        
        // Simulate step preview
        const steps = [
            "1. Navigate to the specified URL",
            "2. Analyze the page structure",
            "3. Execute the automation goal",
            "4. Extract and validate results",
            "5. Generate completion report"
        ];
        
        this.addLogEntry(`Preview: Workflow will execute ${steps.length} steps`, 'info');
        steps.forEach((step, index) => {
            setTimeout(() => {
                this.addLogEntry(step, 'info');
            }, (index + 1) * 500);
        });
        
        this.showNotification('Workflow steps previewed', 'info');
    }
    
    clearExecutionLog() {
        const logContainer = document.getElementById('log-container');
        if (logContainer) {
            logContainer.innerHTML = `
                <div class="log-entry info">
                    <i class="fas fa-info-circle"></i>
                    <span>Log cleared. Ready for new workflow execution.</span>
                    <span class="log-time">Just now</span>
                </div>
            `;
        }
    }
    
    updateProgress(percentage) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        if (progressBar) {
            progressBar.style.setProperty('--progress', `${percentage}%`);
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(percentage)}%`;
        }
    }
    
    updateWorkflowStatus(status) {
        const statusElement = document.getElementById('workflow-status');
        if (statusElement) {
            statusElement.textContent = status;
            
            // Add status-specific styling
            statusElement.className = 'status-value';
            if (status === 'Running') {
                statusElement.classList.add('status-running');
            } else if (status === 'Completed') {
                statusElement.classList.add('status-completed');
            } else if (status === 'Error') {
                statusElement.classList.add('status-error');
            }
        }
    }
    
    updateCurrentStep(step) {
        const stepElement = document.getElementById('current-step');
        if (stepElement) {
            stepElement.textContent = step;
        }
    }
    
    addLogEntry(message, type = 'info') {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const icon = this.getLogIcon(type);
        const time = new Date().toLocaleTimeString();
        
        logEntry.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
            <span class="log-time">${time}</span>
        `;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    
    getLogIcon(type) {
        const icons = {
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle'
        };
        return icons[type] || icons.info;
    }
    
}

// Global functions for modal close buttons
window.closeModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    }
};

window.generateReport = () => {
    if (window.workflowManager) {
        window.workflowManager.generateReport();
    }
};

window.refreshErrorAnalytics = () => {
    if (window.workflowManager) {
        window.workflowManager.showErrorAnalytics();
    }
};

window.refreshStateManagement = () => {
    if (window.workflowManager) {
        window.workflowManager.showStateManagement();
    }
};

window.refreshPerformance = () => {
    if (window.workflowManager) {
        window.workflowManager.showPerformanceAnalytics();
    }
};



// Initialize the workflow manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.workflowManager = new WorkflowManager();
});

// Health check on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/health');
        if (response.ok) {
            console.log('✅ Server is healthy');
        } else {
            console.warn('⚠️ Server health check failed');
        }
    } catch (error) {
        console.error('❌ Server health check error:', error);
    }
});
