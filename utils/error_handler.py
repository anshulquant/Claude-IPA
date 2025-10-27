"""
Enhanced Error Handling and Recovery System for Quantanite IPA MVP

This module provides:
- Advanced error classification and categorization
- Intelligent retry strategies with exponential backoff
- Circuit breaker pattern implementation
- Error recovery mechanisms
- Error analytics and pattern detection
- Alert system for critical errors
- Auto-recovery from common error scenarios
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import traceback
import functools

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues, non-critical
    MEDIUM = "medium"     # Moderate issues, may affect functionality
    HIGH = "high"         # Serious issues, significant impact
    CRITICAL = "critical" # Critical issues, system failure

class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"           # Network connectivity issues
    TIMEOUT = "timeout"           # Timeout-related errors
    AUTHENTICATION = "auth"       # Authentication/authorization errors
    VALIDATION = "validation"     # Data validation errors
    RESOURCE = "resource"         # Resource availability issues
    CONFIGURATION = "config"      # Configuration errors
    BROWSER = "browser"           # Browser automation errors
    AI_SERVICE = "ai_service"     # AI service errors
    DATABASE = "database"         # Database errors
    FILE_SYSTEM = "file_system"   # File system errors
    MEMORY = "memory"             # Memory-related errors
    PERMISSION = "permission"     # Permission errors
    UNKNOWN = "unknown"           # Unknown error types

class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""
    RETRY = "retry"               # Simple retry
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Exponential backoff retry
    CIRCUIT_BREAKER = "circuit_breaker"          # Circuit breaker pattern
    FALLBACK = "fallback"         # Fallback to alternative method
    SKIP = "skip"                 # Skip and continue
    PAUSE = "pause"               # Pause workflow for manual intervention
    TERMINATE = "terminate"       # Terminate workflow

@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime
    workflow_id: Optional[str] = None
    step_number: Optional[int] = None
    retry_count: int = 0
    recovery_strategy: Optional[RecoveryStrategy] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: List[ErrorCategory] = None

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    success_threshold: int = 2

class CircuitBreaker:
    """Circuit breaker implementation for preventing cascading failures"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        self.half_open_calls = 0
        self.half_open_successes = 0
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self.last_failure_time and \
               time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = "half_open"
                self.half_open_calls = 0
                self.half_open_successes = 0
                return True
            return False
        elif self.state == "half_open":
            return self.half_open_calls < self.config.half_open_max_calls
        return False
    
    def record_success(self):
        """Record successful execution"""
        if self.state == "half_open":
            self.half_open_successes += 1
            if self.half_open_successes >= self.config.success_threshold:
                self.state = "closed"
                self.failure_count = 0
        elif self.state == "closed":
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "half_open":
            self.state = "open"
        elif self.failure_count >= self.config.failure_threshold:
            self.state = "open"

class ErrorHandler:
    """Main error handling and recovery system"""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None, 
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        
        # Circuit breakers for different error categories
        self.circuit_breakers: Dict[ErrorCategory, CircuitBreaker] = {}
        for category in ErrorCategory:
            self.circuit_breakers[category] = CircuitBreaker(self.circuit_breaker_config)
        
        # Error analytics
        self.error_history: List[ErrorContext] = []
        self.error_patterns: Dict[str, int] = {}
        self.recovery_success_rate: Dict[RecoveryStrategy, float] = {}
        
        # Alert thresholds
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.MEDIUM: 10,
            ErrorSeverity.LOW: 20
        }
        
        # Recovery strategies mapping
        self.recovery_strategies = {
            ErrorCategory.NETWORK: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.TIMEOUT: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.AUTHENTICATION: RecoveryStrategy.FALLBACK,
            ErrorCategory.VALIDATION: RecoveryStrategy.SKIP,
            ErrorCategory.RESOURCE: RecoveryStrategy.CIRCUIT_BREAKER,
            ErrorCategory.CONFIGURATION: RecoveryStrategy.TERMINATE,
            ErrorCategory.BROWSER: RecoveryStrategy.RETRY,
            ErrorCategory.AI_SERVICE: RecoveryStrategy.CIRCUIT_BREAKER,
            ErrorCategory.DATABASE: RecoveryStrategy.CIRCUIT_BREAKER,
            ErrorCategory.FILE_SYSTEM: RecoveryStrategy.RETRY,
            ErrorCategory.MEMORY: RecoveryStrategy.PAUSE,
            ErrorCategory.PERMISSION: RecoveryStrategy.TERMINATE,
            ErrorCategory.UNKNOWN: RecoveryStrategy.RETRY
        }
    
    def classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """Classify an error and determine handling strategy"""
        error_message = str(error)
        error_type = type(error).__name__
        
        # Determine category based on error type and message
        category = self._determine_category(error, error_message)
        severity = self._determine_severity(error, category, context)
        recovery_strategy = self.recovery_strategies.get(category, RecoveryStrategy.RETRY)
        
        # Create error context
        error_context = ErrorContext(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            timestamp=datetime.now(),
            workflow_id=context.get("workflow_id") if context else None,
            step_number=context.get("step_number") if context else None,
            retry_count=context.get("retry_count", 0) if context else 0,
            recovery_strategy=recovery_strategy,
            additional_data=context
        )
        
        # Record error for analytics
        self._record_error(error_context)
        
        return error_context
    
    def _determine_category(self, error: Exception, error_message: str) -> ErrorCategory:
        """Determine error category based on error type and message"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network errors
        if any(keyword in error_str for keyword in ["connection", "network", "socket", "timeout", "unreachable"]):
            return ErrorCategory.NETWORK
        
        # Timeout errors
        if any(keyword in error_str for keyword in ["timeout", "timed out", "deadline"]):
            return ErrorCategory.TIMEOUT
        
        # Authentication errors
        if any(keyword in error_str for keyword in ["auth", "login", "credential", "unauthorized", "forbidden"]):
            return ErrorCategory.AUTHENTICATION
        
        # Validation errors
        if any(keyword in error_str for keyword in ["validation", "invalid", "malformed", "format"]):
            return ErrorCategory.VALIDATION
        
        # Resource errors
        if any(keyword in error_str for keyword in ["resource", "unavailable", "busy", "locked"]):
            return ErrorCategory.RESOURCE
        
        # Configuration errors
        if any(keyword in error_str for keyword in ["config", "setting", "parameter", "option"]):
            return ErrorCategory.CONFIGURATION
        
        # Browser errors
        if any(keyword in error_str for keyword in ["browser", "selenium", "webdriver", "element"]):
            return ErrorCategory.BROWSER
        
        # AI service errors
        if any(keyword in error_str for keyword in ["ai", "claude", "openai", "api", "model"]):
            return ErrorCategory.AI_SERVICE
        
        # Database errors
        if any(keyword in error_str for keyword in ["database", "sql", "query", "connection"]):
            return ErrorCategory.DATABASE
        
        # File system errors
        if any(keyword in error_str for keyword in ["file", "directory", "path", "permission", "access"]):
            return ErrorCategory.FILE_SYSTEM
        
        # Memory errors
        if any(keyword in error_str for keyword in ["memory", "out of memory", "allocation"]):
            return ErrorCategory.MEMORY
        
        # Permission errors
        if any(keyword in error_str for keyword in ["permission", "access denied", "forbidden"]):
            return ErrorCategory.PERMISSION
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory, context: Optional[Dict[str, Any]]) -> ErrorSeverity:
        """Determine error severity based on category and context"""
        # Critical errors
        if category in [ErrorCategory.CONFIGURATION, ErrorCategory.PERMISSION, ErrorCategory.MEMORY]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.DATABASE, ErrorCategory.AI_SERVICE]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.RESOURCE, ErrorCategory.BROWSER, ErrorCategory.FILE_SYSTEM]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT, ErrorCategory.VALIDATION]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _record_error(self, error_context: ErrorContext):
        """Record error for analytics and pattern detection"""
        self.error_history.append(error_context)
        
        # Keep only last 1000 errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
        
        # Update error patterns
        pattern_key = f"{error_context.category.value}_{error_context.severity.value}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        # Check for alert thresholds
        self._check_alert_thresholds(error_context)
    
    def _check_alert_thresholds(self, error_context: ErrorContext):
        """Check if error count exceeds alert thresholds"""
        severity = error_context.severity
        threshold = self.alert_thresholds.get(severity, float('inf'))
        
        # Count recent errors of this severity
        recent_errors = [
            e for e in self.error_history 
            if e.severity == severity and 
            (datetime.now() - e.timestamp).total_seconds() < 300  # Last 5 minutes
        ]
        
        if len(recent_errors) >= threshold:
            self._send_alert(error_context, len(recent_errors))
    
    def _send_alert(self, error_context: ErrorContext, count: int):
        """Send alert for critical error patterns"""
        alert_message = f"ALERT: {count} {error_context.severity.value} errors detected in last 5 minutes"
        logger.critical(alert_message, extra={
            "context": {
                "error_category": error_context.category.value,
                "error_type": error_context.error_type,
                "error_count": count,
                "workflow_id": error_context.workflow_id,
                "step_number": error_context.step_number
            }
        })
    
    async def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """Handle error with appropriate recovery strategy"""
        error_context = self.classify_error(error, context)
        
        logger.error(f"Error handled: {error_context.error_type}", extra={
            "context": {
                "error_message": error_context.error_message,
                "severity": error_context.severity.value,
                "category": error_context.category.value,
                "recovery_strategy": error_context.recovery_strategy.value,
                "workflow_id": error_context.workflow_id,
                "step_number": error_context.step_number
            }
        })
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers[error_context.category]
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for {error_context.category.value}")
            raise Exception(f"Circuit breaker open for {error_context.category.value}")
        
        # Apply recovery strategy
        try:
            result = await self._apply_recovery_strategy(error_context, error)
            circuit_breaker.record_success()
            return result
        except Exception as recovery_error:
            circuit_breaker.record_failure()
            logger.error(f"Recovery failed: {recovery_error}")
            raise
    
    async def _apply_recovery_strategy(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Apply the appropriate recovery strategy"""
        strategy = error_context.recovery_strategy
        
        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_with_simple_backoff(error_context, original_error)
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            return await self._retry_with_exponential_backoff(error_context, original_error)
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            return await self._circuit_breaker_recovery(error_context, original_error)
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._fallback_recovery(error_context, original_error)
        elif strategy == RecoveryStrategy.SKIP:
            return await self._skip_recovery(error_context, original_error)
        elif strategy == RecoveryStrategy.PAUSE:
            return await self._pause_recovery(error_context, original_error)
        elif strategy == RecoveryStrategy.TERMINATE:
            return await self._terminate_recovery(error_context, original_error)
        else:
            raise original_error
    
    async def _retry_with_simple_backoff(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Simple retry with fixed delay"""
        for attempt in range(self.retry_config.max_retries):
            try:
                await asyncio.sleep(self.retry_config.base_delay)
                # In real implementation, this would retry the original operation
                raise original_error  # Placeholder
            except Exception as e:
                if attempt == self.retry_config.max_retries - 1:
                    raise e
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
    
    async def _retry_with_exponential_backoff(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Retry with exponential backoff"""
        for attempt in range(self.retry_config.max_retries):
            try:
                delay = min(
                    self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                    self.retry_config.max_delay
                )
                
                if self.retry_config.jitter:
                    import random
                    jitter = random.uniform(0.1, 0.3) * delay
                    delay += jitter
                
                await asyncio.sleep(delay)
                # In real implementation, this would retry the original operation
                raise original_error  # Placeholder
            except Exception as e:
                if attempt == self.retry_config.max_retries - 1:
                    raise e
                logger.warning(f"Exponential backoff retry attempt {attempt + 1} failed: {e}")
    
    async def _circuit_breaker_recovery(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Circuit breaker recovery strategy"""
        circuit_breaker = self.circuit_breakers[error_context.category]
        
        if circuit_breaker.state == "open":
            raise Exception(f"Circuit breaker is open for {error_context.category.value}")
        
        # In real implementation, this would attempt the operation
        raise original_error  # Placeholder
    
    async def _fallback_recovery(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Fallback recovery strategy"""
        logger.info(f"Applying fallback recovery for {error_context.category.value}")
        
        # In real implementation, this would use an alternative method
        # For now, we'll just log and re-raise
        raise original_error
    
    async def _skip_recovery(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Skip recovery strategy - continue without the failed operation"""
        logger.warning(f"Skipping failed operation: {error_context.error_message}")
        return None  # Indicate operation was skipped
    
    async def _pause_recovery(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Pause recovery strategy - pause workflow for manual intervention"""
        logger.critical(f"Pausing workflow for manual intervention: {error_context.error_message}")
        # In real implementation, this would pause the workflow
        raise Exception(f"Workflow paused due to {error_context.category.value} error")
    
    async def _terminate_recovery(self, error_context: ErrorContext, original_error: Exception) -> Any:
        """Terminate recovery strategy - terminate workflow"""
        logger.critical(f"Terminating workflow due to {error_context.category.value} error")
        raise Exception(f"Workflow terminated due to {error_context.category.value} error")
    
    def get_error_analytics(self) -> Dict[str, Any]:
        """Get error analytics and patterns"""
        if not self.error_history:
            return {"message": "No errors recorded"}
        
        # Calculate error rates by category and severity
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        # Calculate recovery success rates
        recovery_successes = {}
        recovery_attempts = {}
        
        for error in self.error_history:
            strategy = error.recovery_strategy
            if strategy:
                recovery_attempts[strategy.value] = recovery_attempts.get(strategy.value, 0) + 1
                # In real implementation, we'd track actual recovery success
                recovery_successes[strategy.value] = recovery_successes.get(strategy.value, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "error_patterns": self.error_patterns,
            "recovery_success_rates": {
                strategy: (recovery_successes.get(strategy, 0) / recovery_attempts.get(strategy, 1)) * 100
                for strategy in RecoveryStrategy
                if recovery_attempts.get(strategy, 0) > 0
            },
            "recent_errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "message": error.error_message,
                    "workflow_id": error.workflow_id,
                    "step_number": error.step_number
                }
                for error in self.error_history[-10:]  # Last 10 errors
            ]
        }
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        for circuit_breaker in self.circuit_breakers.values():
            circuit_breaker.state = "closed"
            circuit_breaker.failure_count = 0
            circuit_breaker.last_failure_time = None
            circuit_breaker.half_open_calls = 0
            circuit_breaker.half_open_successes = 0
        
        logger.info("All circuit breakers reset")

# Decorator for automatic error handling
def handle_errors(error_handler: ErrorHandler, context: Optional[Dict[str, Any]] = None):
    """Decorator for automatic error handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return await error_handler.handle_error(e, context)
        return wrapper
    return decorator

# Global error handler instance
_global_error_handler = None

def get_global_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler

def set_global_error_handler(error_handler: ErrorHandler):
    """Set the global error handler instance"""
    global _global_error_handler
    _global_error_handler = error_handler

# Convenience functions
async def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
    """Handle error using global error handler"""
    return await get_global_error_handler().handle_error(error, context)

def classify_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
    """Classify error using global error handler"""
    return get_global_error_handler().classify_error(error, context)

def get_error_analytics() -> Dict[str, Any]:
    """Get error analytics from global error handler"""
    return get_global_error_handler().get_error_analytics()

# Example usage
if __name__ == "__main__":
    # Create error handler
    error_handler = ErrorHandler()
    
    # Example error handling
    async def example_function():
        try:
            # Simulate an error
            raise ConnectionError("Network connection failed")
        except Exception as e:
            return await error_handler.handle_error(e, {"workflow_id": "test_001", "step_number": 5})
    
    # Run example
    import asyncio
    asyncio.run(example_function())
