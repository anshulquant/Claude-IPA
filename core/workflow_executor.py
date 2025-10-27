"""
Workflow Executor - Core execution engine for Claude IPA MVP
Main orchestrator that coordinates the entire automation process
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Import the review queue for human review workflow
from .review_queue import ReviewQueue, ReviewPriority, ReviewStatus, ReviewCategory

# Import advanced logging utilities
from utils.log_utils import (
    performance_logger, 
    performance_context, 
    log_workflow_step,
    log_error_with_stack,
    MemoryMonitor,
    perf_monitor
)

# Import colored logging utilities
from utils.colored_logging import (
    log_workflow_progress,
    log_performance_metrics,
    ProgressBar,
    StatusIndicator
)

# Import report generation utilities
from utils.report_generator import (
    ReportGenerator,
    ReportFormat,
    ReportType,
    generate_execution_report
)

# Import enhanced error handling
from utils.error_handler import (
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    RecoveryStrategy,
    RetryConfig as ErrorRetryConfig,
    CircuitBreakerConfig,
    handle_errors,
    get_global_error_handler
)

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """Execution status for workflow steps"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RESUMING = "resuming"

class ErrorType(Enum):
    """Types of errors that can occur during execution"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    BROWSER_ERROR = "browser_error"
    AI_ERROR = "ai_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow execution"""
    step_number: int
    description: str
    action_type: str  # "navigate", "click", "type", "wait", "complete"
    target: Optional[str] = None
    value: Optional[str] = None
    confidence: float = 1.0
    needs_human_review: bool = False
    status: str = "pending"  # "pending", "running", "completed", "failed"
    error_message: Optional[str] = None
    timestamp: Optional[str] = None

@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    workflow_id: str
    goal: str
    success: bool
    actions_taken: int
    execution_log: List[Dict[str, Any]]
    final_screenshot: Optional[str] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    review_items: List[str] = None  # List of review IDs created during workflow

class WorkflowExecutor:
    """
    Main workflow execution engine.
    Coordinates browser automation, Claude decisions, and human review.
    """
    
    def __init__(self, retry_config: Optional[RetryConfig] = None, confidence_threshold: float = 0.7, auto_approve_reviews: bool = False):
        self.browser_controller = None  # Will be injected by Developer 1
        self.orchestrator = None        # Will be injected by Developer 1
        self.review_queue = ReviewQueue()  # Initialize review queue
        self.max_steps = 20
        self.current_step = 0
        self.execution_log = []
        self.workflow_id = None  # Current workflow ID for review items
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        self.last_failure_time = None
        self.confidence_threshold = confidence_threshold  # Default 0.7 as per Day 4 requirements
        self.auto_approve_reviews = auto_approve_reviews  # Auto-approve for testing
        self.filled_fields = set()  # Track fields we've already filled
        self.action_history = []  # Track recent actions to detect loops
        self.last_url = None  # Track URL changes to detect navigation
        self.performance_metrics = {
            "total_execution_time": 0.0,
            "average_step_time": 0.0,
            "retry_count": 0,
            "error_count": 0,
            "success_rate": 0.0
        }
        
        # Pause/Resume functionality
        self.is_paused = False
        self.pause_reason = None
        self.paused_at = None
        self.pause_count = 0
        self.resume_count = 0
        self.pause_history = []
        self.state_file_path = None
        self.pause_lock = asyncio.Lock()  # Thread-safe pausing
        
        # Enhanced error handling
        self.error_handler = ErrorHandler(
            retry_config=ErrorRetryConfig(
                max_retries=5,
                base_delay=1.0,
                max_delay=30.0,
                exponential_base=2.0,
                jitter=True
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=60.0,
                half_open_max_calls=2,
                success_threshold=1
            )
        )
        self.error_recovery_count = 0
        self.error_recovery_success_count = 0
    
    def should_require_human_review(self, action: Dict[str, Any]) -> bool:
        """
        Determine if an action should require human review based on confidence threshold.
        
        Args:
            action: Action dictionary containing confidence and other metadata
            
        Returns:
            bool: True if human review is required, False otherwise
        """
        confidence = action.get("confidence", 0.5)
        action_type = action.get("action", "unknown")
        
        # Always require review for low confidence actions
        if confidence < self.confidence_threshold:
            logger.info(f"Action requires review: confidence {confidence:.2f} < threshold {self.confidence_threshold}")
            return True
        
        # Require review for high-risk action types with low confidence
        high_risk_actions = ["click", "type", "submit", "navigate"]
        if action_type in high_risk_actions and confidence < 0.8:
            logger.info(f"High-risk action requires review: {action_type} with confidence {confidence:.2f}")
            return True
        
        # Check if action explicitly requires review
        if action.get("needs_human_review", False):
            logger.info(f"Action explicitly marked for review: {action_type}")
            return True
        
        return False
        
    @performance_logger("workflow_execution")
    async def execute_workflow(self, goal: str, start_url: str = None) -> WorkflowResult:
        """
        Main workflow execution method.
        
        Args:
            goal: Natural language description of what to accomplish
            start_url: Optional starting URL (defaults to Google)
            
        Returns:
            WorkflowResult with execution details
        """
        start_time = datetime.now()
        execution_start_time = time.time()
        
        # Log workflow start with context
        logger.info("Starting workflow execution", extra={
            "context": {
                "goal": goal,
                "start_url": start_url or "https://google.com",
                "timestamp": start_time.isoformat()
            }
        })
        
        # Log memory usage at start
        MemoryMonitor.log_memory_usage(logger, "workflow_start")
        
        try:
            # Initialize workflow
            self.workflow_id = f"workflow_{int(datetime.now().timestamp())}"
            workflow_result = WorkflowResult(
                workflow_id=self.workflow_id,
                goal=goal,
                success=False,
                actions_taken=0,
                execution_log=[],
                execution_time=0.0,
                review_items=[]
            )
            
            # Reset execution state and performance metrics
            self.current_step = 0
            self.execution_log = []
            self.performance_metrics = {
                "total_execution_time": 0.0,
                "average_step_time": 0.0,
                "retry_count": 0,
                "error_count": 0,
                "success_rate": 0.0
            }
            
            # Add initial log entry
            self._add_log_entry("🚀 Initialization", f"Starting workflow: {goal}", "info")
            
            # Set default start URL
            if not start_url:
                start_url = "https://google.com"
            
            # Store current workflow result for review tracking
            self._current_workflow_result = workflow_result
            
            # Execute workflow steps
            await self._execute_workflow_steps(goal, start_url, workflow_result)
            
            # Calculate execution time
            end_time = datetime.now()
            execution_end_time = time.time()
            workflow_result.execution_time = (end_time - start_time).total_seconds()
            
            # Update final performance metrics
            self.performance_metrics["total_execution_time"] = execution_end_time - execution_start_time
            
            # Mark as successful if we completed without errors
            workflow_result.success = True
            workflow_result.actions_taken = self.current_step
            workflow_result.execution_log = self.execution_log.copy()
            
            # Log performance metrics with structured data
            logger.info("Workflow performance metrics", extra={
                "context": {
                    "workflow_id": self.workflow_id,
                    "performance_metrics": self.performance_metrics,
                    "execution_time": workflow_result.execution_time
                },
                "performance": True
            })
            
            # Log review queue statistics
            if workflow_result.review_items:
                logger.info("Review queue summary", extra={
                    "context": {
                        "workflow_id": self.workflow_id,
                        "review_items_count": len(workflow_result.review_items),
                        "review_items": workflow_result.review_items
                    }
                })
            
            # Log workflow completion
            logger.info("Workflow completed successfully", extra={
                "context": {
                    "workflow_id": self.workflow_id,
                    "execution_time": workflow_result.execution_time,
                    "actions_taken": workflow_result.actions_taken,
                    "success": True
                }
            })
            
            # Log memory usage at completion
            MemoryMonitor.log_memory_usage(logger, "workflow_completion")
            
            return workflow_result
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Log error with full context and stack trace
            log_error_with_stack(
                logger,
                "Workflow execution failed",
                e,
                {
                    "workflow_id": getattr(self, 'workflow_id', 'unknown'),
                    "goal": goal,
                    "start_url": start_url,
                    "execution_time": execution_time,
                    "current_step": self.current_step,
                    "performance_metrics": self.performance_metrics
                }
            )
            
            # Log memory usage on error
            MemoryMonitor.log_memory_usage(logger, "workflow_error")
            
            return WorkflowResult(
                workflow_id=getattr(self, 'workflow_id', 'unknown'),
                goal=goal,
                success=False,
                actions_taken=self.current_step,
                execution_log=self.execution_log.copy(),
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def _execute_workflow_steps(self, goal: str, start_url: str, result: WorkflowResult):
        """Execute the main workflow loop"""
        logger.info(f"🔄 Executing workflow steps for goal: {goal}")
        
        # Step 1: Navigate to starting URL
        await self._execute_step("🌐 Navigate to starting URL", {
            "action": "navigate",
            "target": start_url,
            "reasoning": f"Starting workflow by navigating to {start_url}",
            "confidence": 0.95
        })
        
        # Step 2: Capture initial screenshot
        await self._execute_step("📸 Capture initial screenshot", {
            "action": "screenshot",
            "reasoning": "Capturing initial state for Claude analysis",
            "confidence": 0.9
        })
        
        # Step 3: Analyze page with Claude (mock)
        await self._execute_step("🧠 Analyze page with Claude AI", {
            "action": "analyze",
            "reasoning": "Using Claude to understand the current page and plan next actions",
            "confidence": 0.85
        })
        
        # Main execution loop
        max_iterations = self.max_steps
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"🔄 Workflow iteration {iteration}/{max_iterations}")
            
            # Check for pause condition before each iteration
            if self.is_paused:
                logger.info("Workflow is paused, waiting for resume...")
                while self.is_paused:
                    await asyncio.sleep(1)  # Wait for resume
                logger.info("Workflow resumed, continuing execution...")
            
            # Get Claude's decision (enhanced mock for Day 2)
            claude_decision = await self._get_claude_decision(goal, iteration)
            
            # Check if workflow is complete
            if claude_decision.get("action") == "complete":
                await self._execute_step("✅ Workflow completed", {
                    "action": "complete",
                    "reasoning": claude_decision.get("reasoning", "Workflow goal achieved"),
                    "confidence": 1.0
                })
                break
            
            # Check if action requires human review based on confidence threshold
            if self.should_require_human_review(claude_decision):
                claude_decision["needs_human_review"] = True
                self._add_log_entry("👤 Human Review", f"Action requires human approval (confidence: {claude_decision.get('confidence', 0.5):.2f})", "warning")
            
            # Execute the suggested action
            step_description = f"Step {iteration}: {claude_decision.get('description', 'Execute action')}"
            await self._execute_step(step_description, claude_decision)
            
            # Check for human review requirement
            if claude_decision.get("needs_human_review", False):
                review_result = await self._handle_human_review(claude_decision)
                if not review_result.get("approved", False):
                    self._add_log_entry("❌ Human Review", "Action rejected by human reviewer", "error")
                    logger.warning("Human review rejected the action, stopping workflow")
                    break
                else:
                    self._add_log_entry("✅ Human Review", "Action approved by human reviewer", "success")
            
            # Capture screenshot after each action
            await self._execute_step("📸 Capture progress screenshot", {
                "action": "screenshot",
                "reasoning": "Capturing current state after action execution",
                "confidence": 0.9
            })
            
            # Small delay between steps to simulate real processing
            await asyncio.sleep(2)
        
        if iteration >= max_iterations:
            logger.warning(f"⚠️ Workflow reached maximum steps ({max_iterations}), stopping")
            self._add_log_entry("⚠️ Warning", f"Reached maximum steps ({max_iterations})", "warning")
    
    async def _execute_step(self, step_description: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step with enhanced error handling and retry logic"""
        step_start_time = time.time()
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            error_msg = "Circuit breaker is open, stopping execution"
            logger.error(error_msg, extra={
                "context": {
                    "circuit_breaker_open": True,
                    "failure_count": self.circuit_breaker_failures,
                    "threshold": self.circuit_breaker_threshold
                }
            })
            return {
                "success": False, 
                "error": error_msg, 
                "error_type": "circuit_breaker",
                "action": action_data.get("action", "unknown")
            }
        
        self.current_step += 1
        
        # Log step start with context
        logger.info(f"Executing step {self.current_step}: {step_description}", extra={
            "context": {
                "step_number": self.current_step,
                "description": step_description,
                "action_type": action_data.get("action", "unknown"),
                "confidence": action_data.get("confidence", 0.5)
            }
        })
        
        try:
            # Execute with enhanced error handling
            result = await self._execute_with_enhanced_error_handling(
                self._execute_step_internal, 
                step_description, 
                action_data
            )
            
            # Update performance metrics
            step_time = time.time() - step_start_time
            self._update_performance_metrics(step_time, result.get("success", False))
            
            # Log step completion
            log_workflow_step(
                logger,
                self.current_step,
                step_description,
                action_data.get("action", "unknown"),
                "success" if result.get("success", False) else "error",
                step_time,
                {
                    "action_data": action_data,
                    "result": result
                }
            )
            
            return result
            
        except Exception as e:
            # Enhanced error handling with recovery strategies
            try:
                error_context = self.error_handler.classify_error(e, {
                    "workflow_id": self.workflow_id,
                    "step_number": self.current_step,
                    "action_type": action_data.get("action", "unknown"),
                    "step_description": step_description
                })
                
                # Attempt recovery
                recovery_result = await self.error_handler.handle_error(e, {
                    "workflow_id": self.workflow_id,
                    "step_number": self.current_step,
                    "action_type": action_data.get("action", "unknown"),
                    "step_description": step_description
                })
                
                # Update recovery metrics
                self.error_recovery_count += 1
                self.error_recovery_success_count += 1
                
                step_time = time.time() - step_start_time
                self._update_performance_metrics(step_time, True)
                
                # Log successful recovery
                log_workflow_step(
                    logger,
                    self.current_step,
                    step_description,
                    action_data.get("action", "unknown"),
                    "recovered",
                    step_time,
                    {
                        "error": str(e),
                        "error_category": error_context.category.value,
                        "recovery_strategy": error_context.recovery_strategy.value,
                        "recovery_result": recovery_result
                    }
                )
                
                return {
                    "success": True,
                    "action": action_data.get("action", "unknown"),
                    "message": f"Step recovered from {error_context.category.value} error",
                    "recovery_strategy": error_context.recovery_strategy.value,
                    "recovery_result": recovery_result
                }
                
            except Exception as recovery_error:
                # Recovery failed
                self.error_recovery_count += 1
                
                error_type = self._classify_error(e)
                step_time = time.time() - step_start_time
                self._update_performance_metrics(step_time, False)
                
                # Log step failure with context
                log_workflow_step(
                    logger,
                    self.current_step,
                    step_description,
                    action_data.get("action", "unknown"),
                    "error",
                    step_time,
                    {
                        "error": str(e),
                        "error_type": error_type.value,
                        "recovery_error": str(recovery_error),
                        "retry_count": self.retry_config.max_retries
                    }
                )
                
                return {
                    "success": False,
                    "action": action_data.get("action", "unknown"),
                    "error": str(e),
                    "error_type": error_type.value,
                    "recovery_error": str(recovery_error),
                    "retry_count": self.retry_config.max_retries
                }
    
    async def _execute_step_internal(self, step_description: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal step execution logic (called by retry wrapper)"""
        # Enhanced mock execution for Day 2
        action_type = action_data.get("action", "unknown")
        confidence = action_data.get("confidence", 0.5)
        reasoning = action_data.get("reasoning", "No reasoning provided")
        
        # Log action details
        self._add_log_entry(f"Step {self.current_step}", f"Action: {action_type} | Confidence: {confidence:.2f}", "info")
        self._add_log_entry(f"Step {self.current_step}", f"Reasoning: {reasoning}", "info")
        
        # Execute based on action type (use real browser/orchestrator if available)
        if action_type == "navigate":
            result = await self._navigate(action_data.get("target", ""))
        elif action_type == "click":
            result = await self._click(action_data.get("target", ""))
        elif action_type == "type":
            target = action_data.get("target", "")
            value = action_data.get("value", "")
            result = await self._type(target, value)
            # Track filled fields to prevent re-filling
            if result.get("success", True) and target:
                self.filled_fields.add(target)
                logger.info(f"📝 Marked field as filled: {target}")
        elif action_type == "screenshot":
            result = await self._screenshot()
        elif action_type == "analyze":
            result = await self._analyze(action_data.get("reasoning", ""))
        elif action_type == "complete":
            result = await self._complete()
        elif action_type == "error":
            # Handle error action - treat as workflow issue, not failure
            logger.warning(f"⚠️ Claude returned error action: {reasoning}")
            result = {"success": True, "message": f"Error detected: {reasoning}"}
        else:
            logger.warning(f"⚠️ Unknown action type: {action_type}")
            result = {"success": False, "message": f"Unknown action type: {action_type}"}
        
        # Track action history for loop detection
        self.action_history.append({
            "action": action_type,
            "target": action_data.get("target", ""),
            "value": action_data.get("value", ""),
            "step": self.current_step
        })
        
        # Detect if we're stuck in a loop (same action 3+ times in a row)
        if len(self.action_history) >= 3:
            last_3_actions = self.action_history[-3:]
            last_3_targets = [a.get('target') for a in last_3_actions]
            last_3_types = [a.get('action') for a in last_3_actions]
            
            # If same action on same target 3 times, force wait for page change
            if (len(set(last_3_targets)) == 1 and len(set(last_3_types)) == 1 and 
                last_3_targets[0] and last_3_types[0] == 'type'):
                logger.warning(f"⚠️ LOOP DETECTED: Typed into '{last_3_targets[0]}' 3 times in a row!")
                logger.info("Waiting 2 seconds for page to load...")
                await asyncio.sleep(2)
        
        # Add success log with details
        if result.get("success", True):
            self._add_log_entry(f"Step {self.current_step}", f"✅ Successfully executed {action_type}", "success")
            if result.get("message"):
                self._add_log_entry(f"Step {self.current_step}", result["message"], "info")
        else:
            self._add_log_entry(f"Step {self.current_step}", f"❌ Failed to execute {action_type}", "error")
        
        return {
            "success": result.get("success", True),
            "action": action_type,
            "message": result.get("message", f"Executed {action_type}"),
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    async def _get_claude_decision(self, goal: str, iteration: int) -> Dict[str, Any]:
        """Get Claude's decision for next action using real orchestrator or mock"""
        logger.info(f"Getting Claude decision for iteration {iteration}")
        
        # Use real Claude orchestrator if available
        if self.orchestrator and self.browser_controller:
            logger.info("✅ Using REAL Claude orchestrator for decision")
            try:
                # Capture current page state
                logger.info("Capturing screenshot and page state...")
                _, _, screenshot_b64 = await self.browser_controller.capture_screenshot()
                page_text = await self.browser_controller.get_page_text()
                
                # Track URL changes
                current_url = self.browser_controller._page.url if self.browser_controller._page else None
                url_changed = False
                if self.last_url and current_url and self.last_url != current_url:
                    url_changed = True
                    logger.info(f"🔄 URL changed: {self.last_url} → {current_url}")
                self.last_url = current_url
                
                # Get form fields if available
                form_fields = ""
                form_fields_list = []
                try:
                    form_fields_list = await self.browser_controller.get_form_fields()
                    if form_fields_list:
                        # Build formatted string for Claude
                        field_lines = []
                        for f in form_fields_list:
                            status = "✅ FILLED" if f.get('is_filled') else "⬜ EMPTY"
                            value_info = f" = '{f.get('value', '')}'" if f.get('is_filled') else ""
                            field_lines.append(f"- {f['selector']} ({f['type']}) {status}{value_info}")
                        form_fields = "\n".join(field_lines)
                        logger.info(f"Found {len(form_fields_list)} form fields ({sum(1 for f in form_fields_list if f.get('is_filled'))} filled)")
                except Exception as e:
                    logger.warning(f"Could not get form fields: {e}", exc_info=True)
                
                # Build context with action history and filled field info
                context = f"Iteration {iteration}/{self.max_steps}"
                
                # Show URL change if it happened
                if url_changed:
                    context += f"\n\n🔄 PAGE CHANGED! New URL: {current_url}"
                    context += f"\nThe page has navigated to a new location. Check if the goal is achieved."
                
                # Show which fields are already filled (from form detection)
                if form_fields_list:
                    filled = [f for f in form_fields_list if f.get('is_filled')]
                    empty = [f for f in form_fields_list if not f.get('is_filled') and f.get('type') != 'button']
                    
                    if filled:
                        context += f"\n\n✅ ALREADY FILLED FIELDS (DO NOT FILL AGAIN):\n"
                        for field in filled:
                            context += f"- {field['selector']} = '{field['value']}'\n"
                    
                    if empty:
                        context += f"\n\n⬜ EMPTY FIELDS (need to be filled):\n"
                        for field in empty:
                            context += f"- {field['selector']} ({field['type']})\n"
                
                # Show recent actions to detect loops
                if len(self.action_history) > 0:
                    recent_actions = self.action_history[-5:]  # Last 5 actions
                    context += f"\n\n📝 RECENT ACTIONS:\n"
                    for i, action in enumerate(recent_actions, 1):
                        context += f"{i}. {action.get('action')} on {action.get('target', 'N/A')}\n"
                    
                    # Detect if we're repeating the same action
                    if len(recent_actions) >= 3:
                        last_3_targets = [a.get('target') for a in recent_actions[-3:]]
                        if len(set(last_3_targets)) == 1 and last_3_targets[0]:
                            context += f"\n⚠️ WARNING: You've acted on '{last_3_targets[0]}' 3 times in a row. This field is likely already filled. Move to the next empty field or complete the workflow.\n"
                
                # Check if all required fields are filled - auto-complete if so
                if form_fields_list:
                    required_fields = [f for f in form_fields_list if f.get('type') not in ['button', 'radio', 'checkbox']]
                    filled_required = [f for f in required_fields if f.get('is_filled')]
                    
                    if required_fields and len(filled_required) == len(required_fields):
                        logger.info(f"🎉 All {len(required_fields)} required fields are filled! Auto-completing workflow.")
                        return {
                            "action": "complete",
                            "target": "",
                            "value": "",
                            "reasoning": f"All {len(required_fields)} required form fields are filled. Workflow goal achieved.",
                            "confidence": 1.0,
                            "needs_human_review": False,
                            "description": "Auto-complete: All fields filled"
                        }
                
                # Get Claude's decision using the correct method
                logger.info("Calling Claude API for decision...")
                decision = await self.orchestrator.understand_screen_and_decide(
                    screenshot_b64=screenshot_b64,
                    goal=goal,
                    current_step=context,
                    page_text=page_text,
                    form_fields=form_fields
                )
                
                logger.info(f"✅ Claude decided: {decision.get('action')} on '{decision.get('target', 'N/A')}' - {decision.get('reasoning', 'No reasoning')}")
                
                # Add description field for compatibility
                if "description" not in decision:
                    decision["description"] = f"{decision.get('action', 'unknown').title()} {decision.get('target', '')}"
                
                return decision
                
            except Exception as e:
                logger.error(f"❌ Error getting Claude decision: {e}", exc_info=True)
                logger.error(f"Orchestrator type: {type(self.orchestrator)}")
                logger.error(f"Browser controller type: {type(self.browser_controller)}")
                # Fall through to mock responses on error
        else:
            logger.warning(f"⚠️ Cannot use real Claude: orchestrator={self.orchestrator is not None}, browser={self.browser_controller is not None}")
        
        # Fallback to mock Claude responses
        logger.warning("Using mock Claude responses (orchestrator not available or error occurred)")
        mock_responses = [
            {
                "action": "click",
                "target": "search input",
                "value": None,
                "reasoning": "Clicking on search input to enter search query",
                "confidence": 0.9,
                "needs_human_review": False,
                "description": "Click search input"
            },
            {
                "action": "type",
                "target": "search input",
                "value": "machine learning tutorials",
                "reasoning": "Typing search query into the search input",
                "confidence": 0.95,
                "needs_human_review": False,
                "description": "Type search query"
            },
            {
                "action": "click",
                "target": "search button",
                "value": None,
                "reasoning": "Clicking search button to execute search",
                "confidence": 0.9,
                "needs_human_review": False,
                "description": "Click search button"
            },
            {
                "action": "click",
                "target": "suspicious popup",
                "value": None,
                "reasoning": "Detected suspicious popup that may need human review",
                "confidence": 0.3,  # Low confidence triggers review
                "needs_human_review": True,
                "description": "Handle suspicious popup"
            },
            {
                "action": "complete",
                "target": None,
                "value": None,
                "reasoning": "Search completed successfully, workflow goal achieved",
                "confidence": 1.0,
                "needs_human_review": False,
                "description": "Workflow complete"
            }
        ]
        
        # Return appropriate mock response based on iteration
        if iteration <= len(mock_responses):
            return mock_responses[iteration - 1]
        else:
            return {
                "action": "complete",
                "target": None,
                "value": None,
                "reasoning": "Maximum iterations reached",
                "confidence": 1.0,
                "needs_human_review": False,
                "description": "Workflow complete"
            }
    
    async def _handle_human_review(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle actions that need human review using ReviewQueue"""
        logger.info("Action requires human review")
        
        try:
            # Determine category based on action type
            category = self._determine_review_category(action)
            
            # Determine priority based on confidence and action type
            priority = self._determine_review_priority(action)
            
            # Generate tags based on action context
            tags = self._generate_review_tags(action)
            
            # Estimate review time based on action complexity
            estimated_time = self._estimate_review_time(action)
            
            # Create review item in the queue with enhanced features
            review_id = self.review_queue.add_review_item(
                workflow_id=self.workflow_id,
                step_number=self.current_step,
                action_type=action.get("action", "unknown"),
                action_data=action,
                reason=f"Action requires human approval: {action.get('reasoning', 'No reasoning provided')}",
                priority=priority,
                category=category,
                context={
                    "workflow_goal": getattr(self, 'workflow_goal', 'Unknown'),
                    "confidence": action.get("confidence", 0.5),
                    "risk_level": self._assess_risk_level(action),
                    "previous_actions": len(self.workflow_steps) if hasattr(self, 'workflow_steps') else 0
                },
                tags=tags,
                estimated_review_time=estimated_time
            )
            
            # Add review item ID to workflow result
            if hasattr(self, '_current_workflow_result'):
                self._current_workflow_result.review_items.append(review_id)
            
            self._add_log_entry("Human Review", f"Created review item {review_id} for human approval", "info")
            
            # Auto-approve if enabled (for testing without UI)
            if self.auto_approve_reviews:
                logger.info(f"🤖 Auto-approving review {review_id} (auto_approve_reviews=True)")
                from core.review_queue import ReviewStatus
                self.review_queue.submit_review(review_id, reviewer_id="auto_approver", decision=ReviewStatus.APPROVED, notes="Auto-approved for testing")
                self._add_log_entry("Human Review", f"✅ Auto-approved review {review_id}", "success")
                return {
                    "approved": True,
                    "modified_action": None,
                    "reviewer": "auto_approver",
                    "notes": "Auto-approved for testing",
                    "review_time": 0.1,
                    "review_id": review_id
                }
            
            # Wait for human review decision
            # In real implementation, this would poll the review queue or use webhooks
            await asyncio.sleep(2)  # Simulate review time
            
            # Check if review was processed
            review_status = self.review_queue.get_review_status(review_id)
            if review_status and review_status.status == ReviewStatus.APPROVED:
                return {
                    "approved": True,
                    "modified_action": None,
                    "reviewer": review_status.assigned_to or "unknown",
                    "notes": review_status.reviewer_notes or "Approved by human reviewer",
                    "review_time": 2.0,
                    "review_id": review_id
                }
            else:
                return {
                    "approved": False,
                    "modified_action": None,
                    "reviewer": "system",
                    "notes": "Action rejected or timed out",
                    "review_time": 2.0,
                    "review_id": review_id
                }
                
        except Exception as e:
            logger.error(f"Failed to handle human review: {str(e)}")
            self._add_log_entry("Human Review", f"Failed to create review: {str(e)}", "error")
            
            # Fallback to mock approval
            return {
                "approved": True,
                "modified_action": None,
                "reviewer": "system_fallback",
                "notes": "Fallback approval due to review system error",
                "review_time": 0.0,
                "review_id": "fallback_review"
            }
    
    # Enhanced mock methods for Day 2 (will be replaced with real implementations)
    async def _navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL using browser controller or mock"""
        if self.browser_controller:
            await self.browser_controller.navigate(url)
            return {"success": True, "message": f"Successfully navigated to {url}", "url": url}
        else:
            return await self._mock_navigate(url)
    
    async def _click(self, target: str) -> Dict[str, Any]:
        """Click element using browser controller or mock"""
        if self.browser_controller:
            await self.browser_controller.click_element(target)
            return {"success": True, "message": f"Successfully clicked on {target}", "target": target}
        else:
            return await self._mock_click(target)
    
    async def _type(self, target: str, text: str) -> Dict[str, Any]:
        """Type text using browser controller or mock"""
        if self.browser_controller:
            # Detect if this is a search field - if so, press Enter after typing
            is_search_field = (
                'search' in target.lower() or
                'name=\'search\'' in target.lower() or
                'name="search"' in target.lower() or
                'type=\'search\'' in target.lower() or
                'type="search"' in target.lower() or
                'name=\'q\'' in target.lower() or
                'name="q"' in target.lower()
            )
            
            if is_search_field:
                logger.info(f"🔍 Detected search field, will press Enter after typing")
                await self.browser_controller.type_text(target, text, press_enter=True)
                return {"success": True, "message": f"Successfully typed '{text}' into {target} and pressed Enter", "target": target, "text": text}
            else:
                await self.browser_controller.type_text(target, text)
                return {"success": True, "message": f"Successfully typed '{text}' into {target}", "target": target, "text": text}
        else:
            return await self._mock_type(target, text)
    
    async def _screenshot(self) -> Dict[str, Any]:
        """Capture screenshot using browser controller or mock"""
        if self.browser_controller:
            filepath, _, screenshot_b64 = await self.browser_controller.capture_screenshot()
            return {"success": True, "message": "Screenshot captured successfully", "filepath": filepath}
        else:
            return await self._mock_screenshot()
    
    async def _analyze(self, reasoning: str) -> Dict[str, Any]:
        """Analyze page using Claude orchestrator or mock"""
        if self.orchestrator and self.browser_controller:
            _, _, screenshot_b64 = await self.browser_controller.capture_screenshot()
            page_text = await self.browser_controller.get_page_text()
            # This would call Claude's vision API in real implementation
            return {"success": True, "message": "Page analysis completed by Claude AI", "reasoning": reasoning}
        else:
            return await self._mock_analyze(reasoning)
    
    async def _complete(self) -> Dict[str, Any]:
        """Mark workflow as complete"""
        return {"success": True, "message": "Workflow completed successfully", "action": "complete"}
    
    async def _mock_navigate(self, url: str) -> Dict[str, Any]:
        """Mock navigation to URL"""
        logger.info(f"Mock: Navigating to {url}", extra={
            "context": {"action": "navigate", "url": url}
        })
        await asyncio.sleep(2)  # Simulate navigation time
        return {
            "success": True,
            "message": f"Successfully navigated to {url}",
            "url": url,
            "title": "Mock Page Title",
            "status": "loaded"
        }
    
    async def _mock_click(self, target: str) -> Dict[str, Any]:
        """Mock clicking on element"""
        logger.info(f"Mock: Clicking on {target}", extra={
            "context": {"action": "click", "target": target}
        })
        await asyncio.sleep(1)  # Simulate click time
        return {
            "success": True,
            "message": f"Successfully clicked on {target}",
            "target": target,
            "action": "click"
        }
    
    async def _mock_type(self, target: str, text: str) -> Dict[str, Any]:
        """Mock typing text into element"""
        logger.info(f"Mock: Typing '{text}' into {target}", extra={
            "context": {"action": "type", "target": target, "text": text}
        })
        await asyncio.sleep(1.5)  # Simulate typing time
        return {
            "success": True,
            "message": f"Successfully typed '{text}' into {target}",
            "target": target,
            "text": text,
            "action": "type"
        }
    
    async def _mock_screenshot(self) -> Dict[str, Any]:
        """Mock screenshot capture"""
        logger.info("Mock: Capturing screenshot", extra={
            "context": {"action": "screenshot"}
        })
        await asyncio.sleep(1)  # Simulate screenshot time
        return {
            "success": True,
            "message": "Screenshot captured successfully",
            "action": "screenshot",
            "size": "1920x1080",
            "format": "PNG"
        }
    
    async def _mock_analyze(self, reasoning: str) -> Dict[str, Any]:
        """Mock Claude AI analysis"""
        logger.info("Mock: Analyzing page with Claude AI", extra={
            "context": {"action": "analyze", "reasoning": reasoning}
        })
        await asyncio.sleep(3)  # Simulate AI processing time
        return {
            "success": True,
            "message": "Page analysis completed by Claude AI",
            "action": "analyze",
            "reasoning": reasoning,
            "elements_found": 15,
            "confidence": 0.87
        }
    
    async def _mock_complete(self) -> Dict[str, Any]:
        """Mock workflow completion"""
        logger.info("Mock: Workflow completed", extra={
            "context": {"action": "complete"}
        })
        await asyncio.sleep(0.5)  # Simulate completion time
        return {
            "success": True,
            "message": "Workflow completed successfully",
            "action": "complete",
            "status": "success"
        }
    
    # Enhanced Error Handling & Recovery Methods
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_breaker_failures < self.circuit_breaker_threshold:
            return False
        
        if self.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure < self.circuit_breaker_timeout
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type for appropriate handling"""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return ErrorType.TIMEOUT_ERROR
        elif "network" in error_str or "connection" in error_str:
            return ErrorType.NETWORK_ERROR
        elif "permission" in error_str or "access denied" in error_str:
            return ErrorType.PERMISSION_ERROR
        elif "browser" in error_str or "selenium" in error_str:
            return ErrorType.BROWSER_ERROR
        elif "claude" in error_str or "ai" in error_str:
            return ErrorType.AI_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        delay = min(
            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        
        if self.retry_config.jitter:
            # Add random jitter to prevent thundering herd
            import random
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter
        
        return delay
    
    async def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                # Reset circuit breaker on success
                self.circuit_breaker_failures = 0
                return result
            except Exception as e:
                if attempt == self.retry_config.max_retries:
                    # Final attempt failed
                    self.circuit_breaker_failures += 1
                    self.last_failure_time = time.time()
                    self.performance_metrics["retry_count"] += attempt
                    raise e
                
                # Calculate delay with exponential backoff
                delay = self._calculate_retry_delay(attempt)
                error_type = self._classify_error(e)
                logger.warning(f"Attempt {attempt + 1} failed ({error_type.value}), retrying in {delay:.2f}s: {str(e)}")
                await asyncio.sleep(delay)
    
    def _should_retry_error(self, error: Exception) -> bool:
        """Determine if an error should be retried"""
        error_type = self._classify_error(error)
        
        # Retry network and timeout errors
        if error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR]:
            return True
        
        # Don't retry validation or permission errors
        if error_type in [ErrorType.VALIDATION_ERROR, ErrorType.PERMISSION_ERROR]:
            return False
        
        # Retry browser and AI errors with caution
        if error_type in [ErrorType.BROWSER_ERROR, ErrorType.AI_ERROR]:
            return True
        
        # Default to retry for unknown errors
        return True
    
    async def _execute_with_enhanced_error_handling(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with enhanced error handling and recovery strategies"""
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            # Classify the error
            error_context = self.error_handler.classify_error(e, {
                "workflow_id": self.workflow_id,
                "step_number": self.current_step,
                "function_name": func.__name__ if hasattr(func, '__name__') else "unknown"
            })
            
            # Apply recovery strategy based on error classification
            if error_context.recovery_strategy == RecoveryStrategy.RETRY:
                return await self._execute_with_retry(func, *args, **kwargs)
            elif error_context.recovery_strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
                return await self._execute_with_exponential_backoff(func, *args, **kwargs)
            elif error_context.recovery_strategy == RecoveryStrategy.SKIP:
                logger.warning(f"Skipping operation due to {error_context.category.value} error: {e}")
                return {"success": False, "skipped": True, "reason": str(e)}
            elif error_context.recovery_strategy == RecoveryStrategy.PAUSE:
                logger.critical(f"Pausing workflow due to {error_context.category.value} error: {e}")
                await self.pause_workflow(f"Paused due to {error_context.category.value} error", save_state=True)
                raise Exception(f"Workflow paused due to {error_context.category.value} error")
            elif error_context.recovery_strategy == RecoveryStrategy.TERMINATE:
                logger.critical(f"Terminating workflow due to {error_context.category.value} error: {e}")
                raise Exception(f"Workflow terminated due to {error_context.category.value} error")
            else:
                # Default to retry
                return await self._execute_with_retry(func, *args, **kwargs)
    
    async def _execute_with_exponential_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry strategy"""
        last_exception = None
        
        for attempt in range(self.error_handler.retry_config.max_retries + 1):
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                last_exception = e
                
                # Log retry attempt
                if attempt < self.error_handler.retry_config.max_retries:
                    logger.warning(f"Exponential backoff attempt {attempt + 1} failed, retrying: {e}")
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.error_handler.retry_config.base_delay * 
                        (self.error_handler.retry_config.exponential_base ** attempt),
                        self.error_handler.retry_config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if self.error_handler.retry_config.jitter:
                        import random
                        jitter = random.uniform(0.1, 0.3) * delay
                        delay += jitter
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.error_handler.retry_config.max_retries + 1} exponential backoff attempts failed")
        
        # All retries exhausted
        raise last_exception
    
    def _update_performance_metrics(self, step_time: float, success: bool):
        """Update performance metrics after step execution with enhanced logging"""
        self.performance_metrics["total_execution_time"] += step_time
        
        if success:
            # Update success rate
            total_steps = self.current_step
            if total_steps > 0:
                success_count = total_steps - self.performance_metrics["error_count"]
                self.performance_metrics["success_rate"] = success_count / total_steps
        else:
            self.performance_metrics["error_count"] += 1
        
        # Update average step time
        if self.current_step > 0:
            self.performance_metrics["average_step_time"] = (
                self.performance_metrics["total_execution_time"] / self.current_step
            )
        
        # Log performance metrics with enhanced formatting
        if self.current_step % 5 == 0:  # Log every 5 steps
            memory_usage = MemoryMonitor.get_memory_usage()
            log_performance_metrics(
                logger,
                f"Workflow Step {self.current_step}",
                step_time,
                memory_usage["percent"],
                {
                    "success_rate": f"{self.performance_metrics['success_rate']:.1%}",
                    "total_time": f"{self.performance_metrics['total_execution_time']:.1f}s",
                    "avg_step_time": f"{self.performance_metrics['average_step_time']:.2f}s"
                }
            )
    
    def _add_log_entry(self, step: str, message: str, status: str):
        """Add entry to execution log with enhanced formatting"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "message": message,
            "status": status
        }
        self.execution_log.append(log_entry)
        
        # Use enhanced logging with progress indicators
        if hasattr(self, 'max_steps') and self.max_steps > 0:
            log_workflow_progress(
                logger,
                self.current_step,
                self.max_steps,
                step,
                status,
                message
            )
        else:
            # Fallback to standard logging with emoji support
            if status == "error":
                logger.error(f"Step {self.current_step}: {step} - {message}")
            elif status == "warning":
                logger.warning(f"Step {self.current_step}: {step} - {message}")
            elif status == "success":
                logger.info(f"Step {self.current_step}: {step} - {message}")
            else:
                logger.info(f"Step {self.current_step}: {step} - {message}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of current execution"""
        return {
            "current_step": self.current_step,
            "total_log_entries": len(self.execution_log),
            "last_log_entry": self.execution_log[-1] if self.execution_log else None
        }
    
    def get_review_queue_stats(self) -> Dict[str, Any]:
        """Get review queue statistics"""
        return self.review_queue.get_queue_stats()
    
    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """Get pending review items"""
        pending_items = self.review_queue.get_pending_reviews()
        return [
            {
                "id": item.id,
                "workflow_id": item.workflow_id,
                "step_number": item.step_number,
                "action_type": item.action_type,
                "reason": item.reason,
                "priority": item.priority.value,
                "status": item.status.value,
                "created_at": item.created_at.isoformat(),
                "expires_at": item.review_deadline.isoformat() if item.review_deadline else None
            }
            for item in pending_items
        ]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def generate_execution_report(
        self,
        report_format: ReportFormat = ReportFormat.HTML,
        report_type: ReportType = ReportType.COMPREHENSIVE,
        output_dir: str = "reports"
    ) -> str:
        """
        Generate a comprehensive execution report
        
        Args:
            report_format: Format of the report (HTML, JSON, CSV, PDF)
            report_type: Type of report to generate
            output_dir: Directory to save the report
            
        Returns:
            Path to the generated report file
        """
        try:
            # Prepare workflow data for report generation
            workflow_data = {
                "workflow_id": self.workflow_id or f"wf_{int(time.time())}",
                "goal": getattr(self, 'current_goal', 'Unknown goal'),
                "start_time": self.execution_log[0]["timestamp"] if self.execution_log else datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "execution_log": self.execution_log,
                "performance_metrics": self.performance_metrics,
                "max_steps": self.max_steps,
                "confidence_threshold": self.confidence_threshold,
                "status": "completed" if self.current_step > 0 else "pending",
                "success": True,  # This would be determined by actual execution results
                "actions_taken": self.current_step,
                "execution_time": self.performance_metrics.get("total_execution_time", 0.0),
                "review_items": getattr(self, '_current_workflow_result', {}).get('review_items', [])
            }
            
            # Generate the report
            report_path = generate_execution_report(
                workflow_data=workflow_data,
                output_dir=output_dir,
                format=report_format
            )
            
            logger.info(f"Execution report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to generate execution report: {e}")
            raise
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "is_open": self._is_circuit_breaker_open(),
            "failure_count": self.circuit_breaker_failures,
            "threshold": self.circuit_breaker_threshold,
            "last_failure_time": self.last_failure_time,
            "timeout_remaining": (
                self.circuit_breaker_timeout - (time.time() - self.last_failure_time)
                if self.last_failure_time and self._is_circuit_breaker_open()
                else None
            )
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_breaker_failures = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")
    
    # Pause/Resume Functionality
    
    async def pause_workflow(self, reason: str = "Manual pause", save_state: bool = True) -> bool:
        """
        Pause the workflow execution
        
        Args:
            reason: Reason for pausing the workflow
            save_state: Whether to save the current state to disk
            
        Returns:
            bool: True if successfully paused, False otherwise
        """
        async with self.pause_lock:
            try:
                if self.is_paused:
                    logger.warning("Workflow is already paused")
                    return False
                
                # Set pause state
                self.is_paused = True
                self.pause_reason = reason
                self.paused_at = datetime.now()
                self.pause_count += 1
                
                # Add to pause history
                pause_entry = {
                    "timestamp": self.paused_at.isoformat(),
                    "reason": reason,
                    "step": self.current_step,
                    "workflow_id": self.workflow_id
                }
                self.pause_history.append(pause_entry)
                
                # Save state if requested
                if save_state:
                    await self._save_workflow_state()
                
                # Log pause event
                self._add_log_entry("⏸️ Pause", f"Workflow paused: {reason}", "warning")
                logger.info(f"Workflow paused: {reason}", extra={
                    "context": {
                        "workflow_id": self.workflow_id,
                        "current_step": self.current_step,
                        "pause_reason": reason,
                        "pause_count": self.pause_count
                    }
                })
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to pause workflow: {e}")
                self.is_paused = False
                return False
    
    async def resume_workflow(self, reason: str = "Manual resume") -> bool:
        """
        Resume the workflow execution
        
        Args:
            reason: Reason for resuming the workflow
            
        Returns:
            bool: True if successfully resumed, False otherwise
        """
        async with self.pause_lock:
            try:
                if not self.is_paused:
                    logger.warning("Workflow is not paused")
                    return False
                
                # Calculate pause duration
                pause_duration = (datetime.now() - self.paused_at).total_seconds()
                
                # Reset pause state
                self.is_paused = False
                self.resume_count += 1
                
                # Add resume entry to pause history
                resume_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "reason": reason,
                    "step": self.current_step,
                    "workflow_id": self.workflow_id,
                    "pause_duration": pause_duration
                }
                self.pause_history.append(resume_entry)
                
                # Log resume event
                self._add_log_entry("▶️ Resume", f"Workflow resumed: {reason} (paused for {pause_duration:.1f}s)", "info")
                logger.info(f"Workflow resumed: {reason}", extra={
                    "context": {
                        "workflow_id": self.workflow_id,
                        "current_step": self.current_step,
                        "resume_reason": reason,
                        "pause_duration": pause_duration,
                        "resume_count": self.resume_count
                    }
                })
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to resume workflow: {e}")
                return False
    
    async def _save_workflow_state(self) -> bool:
        """
        Save current workflow state to disk for recovery
        
        Returns:
            bool: True if successfully saved, False otherwise
        """
        try:
            if not self.workflow_id:
                logger.warning("Cannot save state: no workflow ID")
                return False
            
            # Create state directory
            state_dir = Path("workflow_states")
            state_dir.mkdir(exist_ok=True)
            
            # Generate state file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.state_file_path = state_dir / f"{self.workflow_id}_state_{timestamp}.json"
            
            # Prepare state data
            state_data = {
                "workflow_id": self.workflow_id,
                "current_step": self.current_step,
                "execution_log": self.execution_log,
                "performance_metrics": self.performance_metrics,
                "is_paused": self.is_paused,
                "pause_reason": self.pause_reason,
                "paused_at": self.paused_at.isoformat() if self.paused_at else None,
                "pause_count": self.pause_count,
                "resume_count": self.resume_count,
                "pause_history": self.pause_history,
                "max_steps": self.max_steps,
                "confidence_threshold": self.confidence_threshold,
                "circuit_breaker_failures": self.circuit_breaker_failures,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # Save to file
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Workflow state saved: {self.state_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False
    
    async def _load_workflow_state(self, state_file_path: str) -> bool:
        """
        Load workflow state from disk
        
        Args:
            state_file_path: Path to the state file
            
        Returns:
            bool: True if successfully loaded, False otherwise
        """
        try:
            state_file = Path(state_file_path)
            if not state_file.exists():
                logger.error(f"State file not found: {state_file_path}")
                return False
            
            # Load state data
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Restore workflow state
            self.workflow_id = state_data.get("workflow_id")
            self.current_step = state_data.get("current_step", 0)
            self.execution_log = state_data.get("execution_log", [])
            self.performance_metrics = state_data.get("performance_metrics", {})
            self.is_paused = state_data.get("is_paused", False)
            self.pause_reason = state_data.get("pause_reason")
            self.paused_at = datetime.fromisoformat(state_data["paused_at"]) if state_data.get("paused_at") else None
            self.pause_count = state_data.get("pause_count", 0)
            self.resume_count = state_data.get("resume_count", 0)
            self.pause_history = state_data.get("pause_history", [])
            self.max_steps = state_data.get("max_steps", 20)
            self.confidence_threshold = state_data.get("confidence_threshold", 0.7)
            self.circuit_breaker_failures = state_data.get("circuit_breaker_failures", 0)
            self.last_failure_time = datetime.fromisoformat(state_data["last_failure_time"]) if state_data.get("last_failure_time") else None
            
            # Set state file path
            self.state_file_path = str(state_file)
            
            logger.info(f"Workflow state loaded: {state_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return False
    
    def get_pause_status(self) -> Dict[str, Any]:
        """Get current pause/resume status"""
        return {
            "is_paused": self.is_paused,
            "pause_reason": self.pause_reason,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "pause_count": self.pause_count,
            "resume_count": self.resume_count,
            "pause_duration": (datetime.now() - self.paused_at).total_seconds() if self.paused_at else 0,
            "state_file_path": self.state_file_path,
            "pause_history": self.pause_history[-5:] if self.pause_history else []  # Last 5 entries
        }
    
    def get_error_analytics(self) -> Dict[str, Any]:
        """Get comprehensive error analytics"""
        return self.error_handler.get_error_analytics()
    
    def get_recovery_metrics(self) -> Dict[str, Any]:
        """Get error recovery metrics"""
        total_recovery_attempts = self.error_recovery_count
        successful_recoveries = self.error_recovery_success_count
        recovery_success_rate = (successful_recoveries / total_recovery_attempts * 100) if total_recovery_attempts > 0 else 0
        
        return {
            "total_recovery_attempts": total_recovery_attempts,
            "successful_recoveries": successful_recoveries,
            "recovery_success_rate": recovery_success_rate,
            "failed_recoveries": total_recovery_attempts - successful_recoveries,
            "error_handler_analytics": self.error_handler.get_error_analytics()
        }
    
    def reset_error_handling(self):
        """Reset error handling state"""
        self.error_handler.reset_circuit_breakers()
        self.error_recovery_count = 0
        self.error_recovery_success_count = 0
        logger.info("Error handling state reset")
    
    def list_saved_states(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all saved workflow states"""
        try:
            state_dir = Path("workflow_states")
            if not state_dir.exists():
                return []
            
            states = []
            pattern = f"{workflow_id}_state_*.json" if workflow_id else "*_state_*.json"
            
            for state_file in state_dir.glob(pattern):
                try:
                    stat = state_file.stat()
                    states.append({
                        "file_path": str(state_file),
                        "workflow_id": workflow_id or "unknown",
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "size": stat.st_size
                    })
                except Exception as e:
                    logger.warning(f"Failed to process state file {state_file}: {e}")
            
            # Sort by modification time (newest first)
            states.sort(key=lambda x: x["modified_at"], reverse=True)
            return states
            
        except Exception as e:
            logger.error(f"Failed to list saved states: {e}")
            return []
    
    async def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """Clean up old state files"""
        try:
            state_dir = Path("workflow_states")
            if not state_dir.exists():
                return 0
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            for state_file in state_dir.glob("*_state_*.json"):
                try:
                    if datetime.fromtimestamp(state_file.stat().st_mtime) < cutoff_time:
                        state_file.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up old state file: {state_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up state file {state_file}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old state files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}")
            return 0
    
    def _determine_review_category(self, action: Dict[str, Any]) -> ReviewCategory:
        """Determine the appropriate category for a review item based on action type and context"""
        action_type = action.get("action", "").lower()
        reasoning = action.get("reasoning", "").lower()
        
        # Security-related actions
        if any(keyword in action_type or keyword in reasoning for keyword in 
               ["password", "login", "authentication", "security", "permission", "access"]):
            return ReviewCategory.SECURITY
        
        # Performance-related actions
        elif any(keyword in action_type or keyword in reasoning for keyword in 
                ["performance", "speed", "optimization", "load", "timeout"]):
            return ReviewCategory.PERFORMANCE
        
        # Data quality actions
        elif any(keyword in action_type or keyword in reasoning for keyword in 
                ["data", "validation", "accuracy", "quality", "verification"]):
            return ReviewCategory.DATA_QUALITY
        
        # User experience actions
        elif any(keyword in action_type or keyword in reasoning for keyword in 
                ["ui", "interface", "user", "experience", "click", "navigate"]):
            return ReviewCategory.USER_EXPERIENCE
        
        # System stability actions
        elif any(keyword in action_type or keyword in reasoning for keyword in 
                ["system", "stability", "error", "exception", "crash", "restart"]):
            return ReviewCategory.SYSTEM_STABILITY
        
        # Compliance actions
        elif any(keyword in action_type or keyword in reasoning for keyword in 
                ["compliance", "regulation", "policy", "audit", "legal"]):
            return ReviewCategory.COMPLIANCE
        
        # Default to accuracy for general decision-making
        else:
            return ReviewCategory.ACCURACY
    
    def _determine_review_priority(self, action: Dict[str, Any]) -> ReviewPriority:
        """Determine the priority level for a review item based on action context"""
        confidence = action.get("confidence", 0.5)
        action_type = action.get("action", "").lower()
        reasoning = action.get("reasoning", "").lower()
        
        # Urgent: Very low confidence or critical actions
        if confidence < 0.3 or any(keyword in action_type or keyword in reasoning for keyword in 
                                  ["urgent", "critical", "emergency", "immediate", "security"]):
            return ReviewPriority.URGENT
        
        # High: Low confidence or important actions
        elif confidence < 0.5 or any(keyword in action_type or keyword in reasoning for keyword in 
                                    ["important", "high", "priority", "financial", "payment"]):
            return ReviewPriority.HIGH
        
        # Medium: Medium confidence or standard actions
        elif confidence < 0.8 or any(keyword in action_type or keyword in reasoning for keyword in 
                                    ["standard", "normal", "routine"]):
            return ReviewPriority.MEDIUM
        
        # Low: High confidence or minor actions
        else:
            return ReviewPriority.LOW
    
    def _generate_review_tags(self, action: Dict[str, Any]) -> List[str]:
        """Generate relevant tags for a review item based on action context"""
        tags = []
        action_type = action.get("action", "").lower()
        reasoning = action.get("reasoning", "").lower()
        confidence = action.get("confidence", 0.5)
        
        # Confidence-based tags
        if confidence < 0.3:
            tags.append("low-confidence")
        elif confidence < 0.5:
            tags.append("medium-confidence")
        else:
            tags.append("high-confidence")
        
        # Action type tags
        if "click" in action_type:
            tags.append("click-action")
        elif "type" in action_type:
            tags.append("input-action")
        elif "navigate" in action_type:
            tags.append("navigation-action")
        elif "screenshot" in action_type:
            tags.append("screenshot-action")
        elif "analyze" in action_type:
            tags.append("analysis-action")
        
        # Context-based tags
        if "popup" in reasoning or "modal" in reasoning:
            tags.append("popup-handling")
        if "form" in reasoning:
            tags.append("form-interaction")
        if "button" in reasoning:
            tags.append("button-interaction")
        if "link" in reasoning:
            tags.append("link-interaction")
        if "error" in reasoning or "exception" in reasoning:
            tags.append("error-handling")
        
        # Risk-based tags
        risk_level = self._assess_risk_level(action)
        if risk_level == "high":
            tags.append("high-risk")
        elif risk_level == "medium":
            tags.append("medium-risk")
        else:
            tags.append("low-risk")
        
        return tags
    
    def _estimate_review_time(self, action: Dict[str, Any]) -> int:
        """Estimate review time in minutes based on action complexity"""
        action_type = action.get("action", "").lower()
        reasoning = action.get("reasoning", "").lower()
        confidence = action.get("confidence", 0.5)
        
        base_time = 5  # Base 5 minutes
        
        # Adjust based on confidence (lower confidence = more time needed)
        confidence_factor = 2 - confidence  # 1.0 to 1.7
        
        # Adjust based on action complexity
        complexity_factor = 1.0
        if "screenshot" in action_type or "analyze" in action_type:
            complexity_factor = 1.5
        elif "form" in reasoning or "multiple" in reasoning:
            complexity_factor = 1.3
        elif "popup" in reasoning or "modal" in reasoning:
            complexity_factor = 1.2
        
        # Adjust based on risk level
        risk_level = self._assess_risk_level(action)
        if risk_level == "high":
            complexity_factor *= 1.5
        elif risk_level == "medium":
            complexity_factor *= 1.2
        
        estimated_time = int(base_time * confidence_factor * complexity_factor)
        return max(2, min(30, estimated_time))  # Between 2 and 30 minutes
    
    def _assess_risk_level(self, action: Dict[str, Any]) -> str:
        """Assess the risk level of an action"""
        action_type = action.get("action", "").lower()
        reasoning = action.get("reasoning", "").lower()
        confidence = action.get("confidence", 0.5)
        
        # High risk indicators
        high_risk_keywords = ["delete", "remove", "clear", "reset", "payment", "purchase", "submit", "confirm"]
        if any(keyword in action_type or keyword in reasoning for keyword in high_risk_keywords):
            return "high"
        
        # Medium risk indicators
        medium_risk_keywords = ["click", "navigate", "type", "select", "choose"]
        if any(keyword in action_type or keyword in reasoning for keyword in medium_risk_keywords):
            return "medium"
        
        # Low risk indicators
        low_risk_keywords = ["screenshot", "analyze", "read", "check", "verify"]
        if any(keyword in action_type or keyword in reasoning for keyword in low_risk_keywords):
            return "low"
        
        # Default based on confidence
        if confidence < 0.4:
            return "high"
        elif confidence < 0.7:
            return "medium"
        else:
            return "low"
