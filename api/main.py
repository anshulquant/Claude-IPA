"""
FastAPI server for Quantanite IPA MVP
Main API endpoints for workflow execution and status tracking
"""

import os
import sys
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from pathlib import Path

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from core.review_queue import ReviewPriority, ReviewStatus

# Import advanced logging
from utils.log_utils import (
    setup_advanced_logging,
    log_api_request,
    MemoryMonitor,
    performance_context
)

# Import colored logging
from utils.colored_logging import (
    setup_colored_logging,
    log_performance_metrics,
    StatusIndicator
)

# Import report generation
from utils.report_generator import (
    ReportGenerator,
    ReportFormat,
    ReportType,
    generate_execution_report,
    generate_batch_report
)

# Load environment variables
load_dotenv()

# Setup colored logging
logger = setup_colored_logging(level="INFO", use_colors=True)

# Global workflow storage (in production, use a database)
workflow_storage: Dict[str, Dict[str, Any]] = {}

# Pydantic models
class WorkflowRequest(BaseModel):
    goal: str
    start_url: Optional[str] = None

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    message: str

class WorkflowStatus(BaseModel):
    workflow_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    execution_log: list = []
    error_message: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Quantanite Automation Hub FastAPI server...")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    
    logger.info("Server startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Quantanite Automation Hub server...")

# Create FastAPI app
app = FastAPI(
    title="Quantanite Automation Hub",
    version="1.0.0",
    description="Intelligent Process Automation powered by Quantanite",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request/response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}", extra={
        "context": {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.now().isoformat()
        }
    })
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    log_api_request(
        logger,
        request.method,
        request.url.path,
        response.status_code,
        duration,
        request.headers.get("user-agent"),
        request.client.host if request.client else None
    )
    
    return response

# Mount static files
# Ensure the static directory exists before mounting
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main UI"""
    logger.info("Serving main UI")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/review-queue", response_class=HTMLResponse)
async def review_queue(request: Request):
    """Serve the review queue management UI"""
    logger.info("Serving review queue UI")
    return templates.TemplateResponse("review_queue.html", {"request": request})

@app.post("/api/execute-workflow", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Execute a workflow from the UI"""
    try:
        # Generate unique workflow ID
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log workflow start with context
        logger.info("Starting workflow execution", extra={
            "context": {
                "workflow_id": workflow_id,
                "goal": workflow_request.goal,
                "start_url": workflow_request.start_url,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Log memory usage
        MemoryMonitor.log_memory_usage(logger, "workflow_start")
        
        # Store workflow in memory
        workflow_storage[workflow_id] = {
            "id": workflow_id,
            "goal": workflow_request.goal,
            "start_url": workflow_request.start_url or "https://google.com",
            "status": "starting",
            "progress": 0,
            "current_step": "Initializing workflow...",
            "execution_log": [],
            "created_at": datetime.now().isoformat(),
            "error_message": None
        }
        
        # Start workflow execution in background
        background_tasks.add_task(execute_workflow_background, workflow_id)
        
        logger.info("Workflow execution started successfully", extra={
            "context": {
                "workflow_id": workflow_id,
                "status": "started"
            }
        })
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="started",
            message="Workflow execution started successfully"
        )
        
    except Exception as e:
        logger.error("Error starting workflow", extra={
            "context": {
                "error": str(e),
                "workflow_request": {
                    "goal": workflow_request.goal,
                    "start_url": workflow_request.start_url
                }
            }
        }, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@app.get("/api/workflow-status/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """Get real-time workflow status"""
    if workflow_id not in workflow_storage:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflow_storage[workflow_id]
    return WorkflowStatus(
        workflow_id=workflow_id,
        status=workflow["status"],
        progress=workflow["progress"],
        current_step=workflow["current_step"],
        execution_log=workflow["execution_log"],
        error_message=workflow["error_message"]
    )

@app.get("/api/workflow-history")
async def get_workflow_history():
    """Get list of executed workflows"""
    workflows = []
    for workflow_id, workflow_data in workflow_storage.items():
        workflows.append({
            "id": workflow_id,
            "goal": workflow_data["goal"],
            "status": workflow_data["status"],
            "created_at": workflow_data["created_at"],
            "progress": workflow_data["progress"]
        })
    
    # Sort by creation time (newest first)
    workflows.sort(key=lambda x: x["created_at"], reverse=True)
    return {"workflows": workflows}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Review Queue API Endpoints
@app.get("/api/review-queue/stats")
async def get_review_queue_stats():
    """Get review queue statistics"""
    try:
        # Get stats from the workflow executor's review queue
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        stats = executor.get_review_queue_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting review queue stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get review queue stats: {str(e)}")

@app.get("/api/review-queue/pending")
async def get_pending_reviews():
    """Get pending review items"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        pending_reviews = executor.get_pending_reviews()
        return {"success": True, "pending_reviews": pending_reviews}
    except Exception as e:
        logger.error(f"Error getting pending reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending reviews: {str(e)}")

@app.post("/api/review-queue/{review_id}/assign")
async def assign_reviewer(review_id: str, reviewer_id: str):
    """Assign a reviewer to a review item"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        # Get the review item
        review_item = executor.review_queue.get_review_status(review_id)
        if not review_item:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        # Assign reviewer
        result = executor.review_queue.assign_reviewer(review_id, reviewer_id)
        if result:
            return {"success": True, "message": f"Review {review_id} assigned to {reviewer_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to assign reviewer")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning reviewer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign reviewer: {str(e)}")

@app.post("/api/review-queue/{review_id}/submit")
async def submit_review_decision(review_id: str, decision: bool, reviewer_id: str, notes: Optional[str] = None):
    """Submit a review decision"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        # Submit review decision
        decision_status = ReviewStatus.APPROVED if decision else ReviewStatus.REJECTED
        result = executor.review_queue.submit_review(
            review_id=review_id,
            reviewer_id=reviewer_id,
            decision=decision_status,
            notes=notes
        )
        
        if result:
            status = "approved" if decision else "rejected"
            return {"success": True, "message": f"Review {review_id} {status}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to submit review decision")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting review decision: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit review decision: {str(e)}")

# Enhanced Review Queue API Endpoints
@app.get("/api/review-queue/filter")
async def filter_reviews(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    reviewer_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    tags: Optional[str] = None,
    overdue_only: bool = False
):
    """Filter reviews based on various criteria"""
    try:
        from core.workflow_executor import WorkflowExecutor
        from core.review_queue import ReviewStatus, ReviewPriority, ReviewCategory
        executor = WorkflowExecutor()
        
        # Convert string parameters to enums
        status_enum = ReviewStatus(status) if status else None
        priority_enum = ReviewPriority(priority) if priority else None
        category_enum = ReviewCategory(category) if category else None
        tags_list = tags.split(",") if tags else None
        
        filtered_reviews = executor.review_queue.filter_reviews(
            status=status_enum,
            priority=priority_enum,
            category=category_enum,
            reviewer_id=reviewer_id,
            workflow_id=workflow_id,
            tags=tags_list,
            overdue_only=overdue_only
        )
        
        # Convert to API format
        reviews_data = []
        for item in filtered_reviews:
            reviews_data.append({
                "id": item.id,
                "workflow_id": item.workflow_id,
                "step_number": item.step_number,
                "action_type": item.action_type,
                "reason": item.reason,
                "priority": item.priority.value,
                "category": item.category.value,
                "status": item.status.value,
                "created_at": item.created_at.isoformat(),
                "assigned_to": item.assigned_to,
                "tags": item.tags,
                "estimated_review_time": item.estimated_review_time,
                "is_overdue": executor.review_queue._is_overdue(item)
            })
        
        return {"success": True, "reviews": reviews_data, "count": len(reviews_data)}
        
    except Exception as e:
        logger.error(f"Error filtering reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to filter reviews: {str(e)}")

@app.get("/api/review-queue/search")
async def search_reviews(query: str):
    """Search reviews by text query"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        search_results = executor.review_queue.search_reviews(query)
        
        # Convert to API format
        reviews_data = []
        for item in search_results:
            reviews_data.append({
                "id": item.id,
                "workflow_id": item.workflow_id,
                "step_number": item.step_number,
                "action_type": item.action_type,
                "reason": item.reason,
                "priority": item.priority.value,
                "category": item.category.value,
                "status": item.status.value,
                "created_at": item.created_at.isoformat(),
                "assigned_to": item.assigned_to,
                "tags": item.tags
            })
        
        return {"success": True, "reviews": reviews_data, "count": len(reviews_data), "query": query}
        
    except Exception as e:
        logger.error(f"Error searching reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search reviews: {str(e)}")

@app.post("/api/review-queue/batch-approve")
async def batch_approve_reviews(review_ids: List[str], reviewer_id: str, notes: Optional[str] = None):
    """Approve multiple review items in batch"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        results = executor.review_queue.batch_approve(review_ids, reviewer_id, notes)
        successful = sum(1 for success in results.values() if success)
        
        return {
            "success": True,
            "message": f"Approved {successful}/{len(review_ids)} items successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error batch approving reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to batch approve reviews: {str(e)}")

@app.post("/api/review-queue/batch-reject")
async def batch_reject_reviews(review_ids: List[str], reviewer_id: str, notes: Optional[str] = None):
    """Reject multiple review items in batch"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        results = executor.review_queue.batch_reject(review_ids, reviewer_id, notes)
        successful = sum(1 for success in results.values() if success)
        
        return {
            "success": True,
            "message": f"Rejected {successful}/{len(review_ids)} items successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error batch rejecting reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to batch reject reviews: {str(e)}")

@app.post("/api/review-queue/export")
async def export_review_data():
    """Export all review data to JSON file"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"review_export_{timestamp}.json"
        filepath = f"logs/{filename}"
        
        success = executor.review_queue.export_review_data(filepath)
        
        if success:
            return {
                "success": True,
                "message": f"Data exported successfully to {filepath}",
                "filepath": filepath
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to export data")
        
    except Exception as e:
        logger.error(f"Error exporting review data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export review data: {str(e)}")

@app.get("/api/review-queue/categories")
async def get_review_categories():
    """Get available review categories"""
    try:
        from core.review_queue import ReviewCategory
        categories = [{"value": cat.value, "name": cat.value.replace("_", " ").title()} for cat in ReviewCategory]
        return {"success": True, "categories": categories}
    except Exception as e:
        logger.error(f"Error getting review categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get review categories: {str(e)}")

@app.get("/api/review-queue/priorities")
async def get_review_priorities():
    """Get available review priorities"""
    try:
        from core.review_queue import ReviewPriority
        priorities = [{"value": pri.value, "name": pri.value.title()} for pri in ReviewPriority]
        return {"success": True, "priorities": priorities}
    except Exception as e:
        logger.error(f"Error getting review priorities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get review priorities: {str(e)}")

# Report Generation API Endpoints
@app.post("/api/reports/generate")
async def generate_workflow_report(
    workflow_id: str,
    format: str = "html",
    report_type: str = "comprehensive"
):
    """Generate a report for a specific workflow execution"""
    try:
        # Get workflow data from storage
        if workflow_id not in workflow_storage:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow_data = workflow_storage[workflow_id]
        
        # Convert string parameters to enums
        report_format = ReportFormat(format.lower())
        report_type_enum = ReportType(report_type.lower())
        
        # Generate report
        report_generator = ReportGenerator()
        report_path = report_generator.generate_execution_report(
            workflow_data=workflow_data,
            report_type=report_type_enum,
            format=report_format
        )
        
        return {
            "success": True,
            "report_path": report_path,
            "workflow_id": workflow_id,
            "format": format,
            "report_type": report_type
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{workflow_id}")
async def get_workflow_report(workflow_id: str, format: str = "html"):
    """Get a generated report for a workflow"""
    try:
        # Convert format to enum
        report_format = ReportFormat(format.lower())
        
        # Determine report directory based on format
        format_dir = {
            ReportFormat.HTML: "html",
            ReportFormat.JSON: "json",
            ReportFormat.CSV: "csv",
            ReportFormat.PDF: "pdf"
        }[report_format]
        
        # Look for report files
        reports_dir = Path("reports") / format_dir
        report_files = list(reports_dir.glob(f"*{workflow_id}*"))
        
        if not report_files:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Return the most recent report
        latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
        
        if report_format == ReportFormat.HTML:
            # Return HTML content
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        
        elif report_format == ReportFormat.JSON:
            # Return JSON content
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return content
        
        else:
            # Return file path for download
            return {
                "success": True,
                "report_path": str(latest_report),
                "download_url": f"/api/reports/{workflow_id}/download?format={format}"
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid format: {e}")
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/list")
async def list_available_reports():
    """List all available reports"""
    try:
        reports = []
        reports_dir = Path("reports")
        
        # Scan all format directories
        for format_dir in ["html", "json", "csv", "pdf"]:
            format_path = reports_dir / format_dir
            if format_path.exists():
                for report_file in format_path.glob("*"):
                    if report_file.is_file():
                        reports.append({
                            "filename": report_file.name,
                            "format": format_dir,
                            "path": str(report_file),
                            "size": report_file.stat().st_size,
                            "created": datetime.fromtimestamp(report_file.stat().st_ctime).isoformat(),
                            "modified": datetime.fromtimestamp(report_file.stat().st_mtime).isoformat()
                        })
        
        return {
            "success": True,
            "total_reports": len(reports),
            "reports": reports
        }
        
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/batch")
async def generate_batch_report_endpoint(
    workflow_ids: List[str],
    format: str = "html"
):
    """Generate a batch report for multiple workflows"""
    try:
        # Get workflow data for specified IDs
        workflows_data = []
        for workflow_id in workflow_ids:
            if workflow_id in workflow_storage:
                workflows_data.append(workflow_storage[workflow_id])
            else:
                logger.warning(f"Workflow {workflow_id} not found in storage")
        
        if not workflows_data:
            raise HTTPException(status_code=404, detail="No valid workflows found")
        
        # Convert format to enum
        report_format = ReportFormat(format.lower())
        
        # Generate batch report
        report_path = generate_batch_report(
            workflows_data=workflows_data,
            output_dir="reports",
            format=report_format
        )
        
        return {
            "success": True,
            "report_path": report_path,
            "workflow_count": len(workflows_data),
            "format": format
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid format: {e}")
    except Exception as e:
        logger.error(f"Failed to generate batch report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Pause/Resume API Endpoints
@app.post("/api/workflow/{workflow_id}/pause")
async def pause_workflow(workflow_id: str, reason: str = "Manual pause via API"):
    """Pause a running workflow"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance (in real implementation, this would be managed globally)
        executor = WorkflowExecutor()
        
        # Check if workflow exists in storage
        if workflow_id not in workflow_storage:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Pause the workflow
        success = await executor.pause_workflow(reason=reason, save_state=True)
        
        if success:
            # Update workflow storage
            workflow_storage[workflow_id]["status"] = "paused"
            workflow_storage[workflow_id]["pause_reason"] = reason
            workflow_storage[workflow_id]["paused_at"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "message": f"Workflow {workflow_id} paused successfully",
                "pause_reason": reason,
                "paused_at": workflow_storage[workflow_id]["paused_at"]
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to pause workflow")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")

@app.post("/api/workflow/{workflow_id}/resume")
async def resume_workflow(workflow_id: str, reason: str = "Manual resume via API"):
    """Resume a paused workflow"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance (in real implementation, this would be managed globally)
        executor = WorkflowExecutor()
        
        # Check if workflow exists in storage
        if workflow_id not in workflow_storage:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Resume the workflow
        success = await executor.resume_workflow(reason=reason)
        
        if success:
            # Update workflow storage
            workflow_storage[workflow_id]["status"] = "running"
            workflow_storage[workflow_id]["resume_reason"] = reason
            workflow_storage[workflow_id]["resumed_at"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "message": f"Workflow {workflow_id} resumed successfully",
                "resume_reason": reason,
                "resumed_at": workflow_storage[workflow_id]["resumed_at"]
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to resume workflow")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")

@app.get("/api/workflow/{workflow_id}/pause-status")
async def get_pause_status(workflow_id: str):
    """Get pause/resume status of a workflow"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Check if workflow exists in storage
        if workflow_id not in workflow_storage:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get pause status
        pause_status = executor.get_pause_status()
        
        # Add workflow storage info
        workflow_info = workflow_storage[workflow_id]
        pause_status.update({
            "workflow_id": workflow_id,
            "workflow_status": workflow_info.get("status"),
            "current_step": workflow_info.get("current_step"),
            "progress": workflow_info.get("progress", 0)
        })
        
        return {
            "success": True,
            "pause_status": pause_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pause status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pause status: {str(e)}")

@app.get("/api/workflow-states")
async def list_workflow_states(workflow_id: Optional[str] = None):
    """List all saved workflow states"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # List saved states
        states = executor.list_saved_states(workflow_id)
        
        return {
            "success": True,
            "states": states,
            "total_count": len(states)
        }
        
    except Exception as e:
        logger.error(f"Error listing workflow states: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflow states: {str(e)}")

@app.post("/api/workflow-states/{state_file}/load")
async def load_workflow_state(state_file: str):
    """Load a workflow from a saved state file"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Load state
        success = await executor._load_workflow_state(state_file)
        
        if success:
            return {
                "success": True,
                "message": f"Workflow state loaded from {state_file}",
                "workflow_id": executor.workflow_id,
                "current_step": executor.current_step,
                "is_paused": executor.is_paused
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to load workflow state")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading workflow state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load workflow state: {str(e)}")

@app.post("/api/workflow-states/cleanup")
async def cleanup_old_states(max_age_hours: int = 24):
    """Clean up old workflow state files"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Cleanup old states
        cleaned_count = await executor.cleanup_old_states(max_age_hours)
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} old state files",
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old states: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old states: {str(e)}")

# Error Handling API Endpoints
@app.get("/api/error-analytics")
async def get_error_analytics():
    """Get comprehensive error analytics"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Get error analytics
        analytics = executor.get_error_analytics()
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting error analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get error analytics: {str(e)}")

@app.get("/api/recovery-metrics")
async def get_recovery_metrics():
    """Get error recovery metrics"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Get recovery metrics
        metrics = executor.get_recovery_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting recovery metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recovery metrics: {str(e)}")

@app.post("/api/error-handling/reset")
async def reset_error_handling():
    """Reset error handling state"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Reset error handling
        executor.reset_error_handling()
        
        return {
            "success": True,
            "message": "Error handling state reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Error resetting error handling: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset error handling: {str(e)}")

@app.post("/api/error-handling/test")
async def test_error_handling(error_type: str = "network", severity: str = "medium"):
    """Test error handling with different error types"""
    try:
        from core.workflow_executor import WorkflowExecutor
        from utils.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Create test error based on type
        if error_type == "network":
            test_error = ConnectionError("Test network connection failed")
        elif error_type == "timeout":
            test_error = TimeoutError("Test timeout occurred")
        elif error_type == "validation":
            test_error = ValueError("Test validation error")
        elif error_type == "permission":
            test_error = PermissionError("Test permission denied")
        elif error_type == "memory":
            test_error = MemoryError("Test memory allocation failed")
        else:
            test_error = Exception(f"Test {error_type} error")
        
        # Test error handling
        try:
            result = await executor.error_handler.handle_error(test_error, {
                "workflow_id": "test_workflow",
                "step_number": 1,
                "test_mode": True
            })
            
            return {
                "success": True,
                "message": f"Error handling test completed for {error_type} error",
                "error_type": error_type,
                "severity": severity,
                "result": result
            }
            
        except Exception as handled_error:
            return {
                "success": True,
                "message": f"Error handling test completed for {error_type} error (handled)",
                "error_type": error_type,
                "severity": severity,
                "handled_error": str(handled_error)
            }
        
    except Exception as e:
        logger.error(f"Error testing error handling: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test error handling: {str(e)}")

@app.get("/api/error-patterns")
async def get_error_patterns():
    """Get error patterns and trends"""
    try:
        from core.workflow_executor import WorkflowExecutor
        
        # Create executor instance
        executor = WorkflowExecutor()
        
        # Get error analytics
        analytics = executor.get_error_analytics()
        
        # Extract patterns
        patterns = {
            "most_common_category": max(analytics.get("category_distribution", {}), key=analytics.get("category_distribution", {}).get) if analytics.get("category_distribution") else None,
            "most_common_severity": max(analytics.get("severity_distribution", {}), key=analytics.get("severity_distribution", {}).get) if analytics.get("severity_distribution") else None,
            "total_errors": analytics.get("total_errors", 0),
            "recent_errors": analytics.get("recent_errors", []),
            "error_patterns": analytics.get("error_patterns", {}),
            "recovery_success_rates": analytics.get("recovery_success_rates", {})
        }
        
        return {
            "success": True,
            "patterns": patterns
        }
        
    except Exception as e:
        logger.error(f"Error getting error patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get error patterns: {str(e)}")


async def execute_workflow_background(workflow_id: str):
    """Background task to execute workflow"""
    with performance_context(f"workflow_background_{workflow_id}", logger):
        try:
            logger.info("Starting background execution", extra={
                "context": {
                    "workflow_id": workflow_id,
                    "status": "starting"
                }
            })
            
            # Update status
            workflow_storage[workflow_id]["status"] = "running"
            workflow_storage[workflow_id]["current_step"] = "Setting up browser automation..."
            
            # Add log entry
            workflow_storage[workflow_id]["execution_log"].append({
                "timestamp": datetime.now().isoformat(),
                "step": "Initialization",
                "message": "Starting workflow execution",
                "status": "info"
            })
            
            # Execute workflow with performance monitoring
            await simulate_workflow_execution(workflow_id)
            
            # Mark as completed
            workflow_storage[workflow_id]["status"] = "completed"
            workflow_storage[workflow_id]["progress"] = 100
            workflow_storage[workflow_id]["current_step"] = "Workflow completed successfully"
            
            logger.info("Workflow completed successfully", extra={
                "context": {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "progress": 100
                }
            })
            
        except Exception as e:
            logger.error("Error executing workflow", extra={
                "context": {
                    "workflow_id": workflow_id,
                    "error": str(e),
                    "status": "failed"
                }
            }, exc_info=True)
            
            workflow_storage[workflow_id]["status"] = "failed"
            workflow_storage[workflow_id]["error_message"] = str(e)
            workflow_storage[workflow_id]["current_step"] = f"Error: {str(e)}"

async def simulate_workflow_execution(workflow_id: str):
    """Execute workflow using real BrowserController and ClaudeOrchestrator"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.workflow_executor import WorkflowExecutor
    from core.browser_controller import BrowserController
    from core.orchestrator import ClaudeOrchestrator
    
    workflow = workflow_storage[workflow_id]
    goal = workflow["goal"]
    start_url = workflow.get("start_url", "https://google.com")
    
    # Create WorkflowExecutor instance with REAL browser and orchestrator
    executor = WorkflowExecutor(auto_approve_reviews=True)  # Auto-approve until UI is ready
    executor.browser_controller = BrowserController(headless=True)  # Use headless for server
    executor.orchestrator = ClaudeOrchestrator()
    
    try:
        # Start the browser
        await executor.browser_controller.start()
        
        # Execute the workflow
        result = await executor.execute_workflow(goal, start_url)
        
        # Update workflow with results
        workflow["progress"] = 100 if result.success else 50
        workflow["current_step"] = "Workflow completed" if result.success else "Workflow failed"
        workflow["execution_log"] = result.execution_log
        workflow["success"] = result.success
        workflow["actions_taken"] = result.actions_taken
        workflow["execution_time"] = result.execution_time
        
        if not result.success and result.error_message:
            workflow["error_message"] = result.error_message
        
        logger.info(f"Workflow {workflow_id} completed: success={result.success}, actions={result.actions_taken}")
        
    except Exception as e:
        logger.error(f"Error in workflow execution: {str(e)}")
        workflow["current_step"] = f"Error: {str(e)}"
        workflow["error_message"] = str(e)
        workflow["progress"] = 0
    finally:
        # Always close the browser
        if executor.browser_controller:
            await executor.browser_controller.close()

# Specific Review Item Routes (must be after general routes)
@app.get("/api/review-queue/{review_id}")
async def get_review_item(review_id: str):
    """Get a specific review item"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        review_item = executor.review_queue.get_review_status(review_id)
        if not review_item:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        return {
            "success": True,
            "review_item": {
                "id": review_item.id,
                "workflow_id": review_item.workflow_id,
                "step_number": review_item.step_number,
                "action_type": review_item.action_type,
                "action_data": review_item.action_data,
                "reason": review_item.reason,
                "priority": review_item.priority.value,
                "status": review_item.status.value,
                "created_at": review_item.created_at.isoformat(),
                "expires_at": review_item.expires_at.isoformat() if review_item.expires_at else None,
                "assigned_to": review_item.assigned_to,
                "review_notes": review_item.review_notes,
                "reviewed_at": review_item.reviewed_at.isoformat() if review_item.reviewed_at else None,
                "decision": review_item.decision
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get review item: {str(e)}")

@app.get("/api/review-queue/{review_id}/history")
async def get_review_history(review_id: str):
    """Get the history of a specific review item"""
    try:
        from core.workflow_executor import WorkflowExecutor
        executor = WorkflowExecutor()
        
        history = executor.review_queue.get_review_history(review_id)
        if history is None:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        return {
            "success": True,
            "history": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "action": entry.action,
                    "user": entry.user,
                    "notes": entry.notes
                }
                for entry in history
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get review history: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")  # Changed from 0.0.0.0 to 127.0.0.1
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
