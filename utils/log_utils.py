"""
Logging Utilities for Claude IPA MVP

This module provides utility functions for:
- Performance monitoring and logging
- Memory usage tracking
- Log sanitization and formatting
- Error tracking and reporting
- Log analysis and reporting
"""

import os
import sys
import time
import psutil
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation}_{int(time.time() * 1000)}"
        self.start_times[timer_id] = time.time()
        return timer_id
    
    def end_timer(self, timer_id: str, operation: str = None) -> float:
        """End timing and return duration"""
        if timer_id not in self.start_times:
            logger.warning(f"Timer {timer_id} not found")
            return 0.0
        
        duration = time.time() - self.start_times[timer_id]
        del self.start_times[timer_id]
        
        if operation:
            self.record_metric(operation, duration)
        
        return duration
    
    def record_metric(self, operation: str, value: float, unit: str = "seconds"):
        """Record a performance metric"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append({
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {}
        for operation, values in self.metrics.items():
            if values:
                durations = [v["value"] for v in values]
                summary[operation] = {
                    "count": len(durations),
                    "total": sum(durations),
                    "average": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "last": durations[-1] if durations else 0
                }
        return summary
    
    def log_metrics_summary(self):
        """Log all metrics summary"""
        summary = self.get_metrics_summary()
        for operation, stats in summary.items():
            logger.info(f"Performance metrics for {operation}: {stats}", extra={
                "context": {"operation": operation, "metrics": stats},
                "performance": True
            })

# Global performance monitor
perf_monitor = PerformanceMonitor()

class MemoryMonitor:
    """Monitor memory usage"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss,  # Resident Set Size
            "vms": memory_info.vms,  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available": psutil.virtual_memory().available,
            "total": psutil.virtual_memory().total,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def log_memory_usage(logger: logging.Logger, context: str = ""):
        """Log current memory usage"""
        memory = MemoryMonitor.get_memory_usage()
        logger.info(f"Memory usage {context}: {memory['percent']:.1f}%", extra={
            "context": {"memory": memory, "context": context},
            "performance": True
        })

def performance_logger(operation: str = None):
    """Decorator to log function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            timer_id = perf_monitor.start_timer(op_name)
            
            try:
                result = func(*args, **kwargs)
                duration = perf_monitor.end_timer(timer_id, op_name)
                
                logger.info(f"Function {op_name} completed in {duration:.3f}s", extra={
                    "context": {"operation": op_name, "duration": duration},
                    "performance": True
                })
                
                return result
            except Exception as e:
                duration = perf_monitor.end_timer(timer_id, op_name)
                logger.error(f"Function {op_name} failed after {duration:.3f}s: {str(e)}", extra={
                    "context": {"operation": op_name, "duration": duration, "error": str(e)},
                    "performance": True
                })
                raise
        
        return wrapper
    return decorator

@contextmanager
def performance_context(operation: str, logger: logging.Logger = None):
    """Context manager for performance logging"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    timer_id = perf_monitor.start_timer(operation)
    start_memory = MemoryMonitor.get_memory_usage()
    
    try:
        yield
    finally:
        duration = perf_monitor.end_timer(timer_id, operation)
        end_memory = MemoryMonitor.get_memory_usage()
        
        memory_delta = end_memory["rss"] - start_memory["rss"]
        
        logger.info(f"Operation {operation} completed in {duration:.3f}s", extra={
            "context": {
                "operation": operation,
                "duration": duration,
                "memory_delta": memory_delta,
                "start_memory": start_memory,
                "end_memory": end_memory
            },
            "performance": True
        })

def sanitize_log_data(data: Any) -> Any:
    """Sanitize data for logging (remove sensitive information)"""
    if isinstance(data, dict):
        sanitized = {}
        sensitive_keys = ['password', 'token', 'key', 'secret', 'auth', 'credential']
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_log_data(value)
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    
    elif isinstance(data, str):
        # Remove potential sensitive patterns
        import re
        patterns = [
            (r'password["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'password[REDACTED]'),
            (r'token["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'token[REDACTED]'),
            (r'key["\']?\s*[:=]\s*["\']?[^"\']+["\']?', r'key[REDACTED]'),
        ]
        
        sanitized = data
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    else:
        return data

def log_workflow_step(
    logger: logging.Logger,
    step_number: int,
    description: str,
    action_type: str,
    status: str,
    duration: float = None,
    context: Dict[str, Any] = None
):
    """Log a workflow step with structured data"""
    log_context = {
        "step_number": step_number,
        "description": description,
        "action_type": action_type,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    if duration is not None:
        log_context["duration"] = duration
    
    if context:
        log_context["context"] = sanitize_log_data(context)
    
    # Choose log level based on status
    if status == "error":
        logger.error(f"Step {step_number}: {description} - {status}", extra={
            "context": log_context
        })
    elif status == "warning":
        logger.warning(f"Step {step_number}: {description} - {status}", extra={
            "context": log_context
        })
    elif status == "success":
        logger.info(f"Step {step_number}: {description} - {status}", extra={
            "context": log_context
        })
    else:
        logger.info(f"Step {step_number}: {description} - {status}", extra={
            "context": log_context
        })

def log_error_with_stack(
    logger: logging.Logger,
    message: str,
    error: Exception,
    context: Dict[str, Any] = None
):
    """Log error with full stack trace and context"""
    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "stack_trace": traceback.format_exc(),
        "timestamp": datetime.now().isoformat()
    }
    
    if context:
        error_context["context"] = sanitize_log_data(context)
    
    logger.error(message, extra={
        "context": error_context
    }, exc_info=True)

def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_agent: str = None,
    ip_address: str = None
):
    """Log API request with performance data"""
    context = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration": duration,
        "timestamp": datetime.now().isoformat()
    }
    
    if user_agent:
        context["user_agent"] = user_agent
    
    if ip_address:
        context["ip_address"] = ip_address
    
    # Choose log level based on status code
    if status_code >= 500:
        logger.error(f"API {method} {path} - {status_code} ({duration:.3f}s)", extra={
            "context": context
        })
    elif status_code >= 400:
        logger.warning(f"API {method} {path} - {status_code} ({duration:.3f}s)", extra={
            "context": context
        })
    else:
        logger.info(f"API {method} {path} - {status_code} ({duration:.3f}s)", extra={
            "context": context
        })

class LogAnalyzer:
    """Analyze log files for patterns and insights"""
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
    
    def analyze_errors(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze errors in the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        errors = []
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'ERROR' in line:
                        # Parse timestamp and check if within range
                        try:
                            timestamp_str = line.split(' - ')[0]
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if timestamp >= cutoff_time:
                                errors.append(line.strip())
                        except:
                            continue
        
        except FileNotFoundError:
            logger.warning(f"Log file {self.log_file_path} not found")
            return {"error": "Log file not found"}
        
        # Categorize errors
        error_categories = {}
        for error in errors:
            if 'timeout' in error.lower():
                error_categories['timeout'] = error_categories.get('timeout', 0) + 1
            elif 'network' in error.lower():
                error_categories['network'] = error_categories.get('network', 0) + 1
            elif 'permission' in error.lower():
                error_categories['permission'] = error_categories.get('permission', 0) + 1
            else:
                error_categories['other'] = error_categories.get('other', 0) + 1
        
        return {
            "total_errors": len(errors),
            "time_period_hours": hours,
            "error_categories": error_categories,
            "recent_errors": errors[-10:] if errors else []
        }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary from logs"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        performance_logs = []
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'Performance:' in line and 'INFO' in line:
                        try:
                            timestamp_str = line.split(' - ')[0]
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if timestamp >= cutoff_time:
                                performance_logs.append(line.strip())
                        except:
                            continue
        
        except FileNotFoundError:
            return {"error": "Log file not found"}
        
        # Extract performance data
        durations = []
        operations = {}
        
        for log in performance_logs:
            if 'completed in' in log:
                try:
                    # Extract duration from log
                    duration_str = log.split('completed in ')[1].split('s')[0]
                    duration = float(duration_str)
                    durations.append(duration)
                    
                    # Extract operation name
                    operation = log.split('Performance: ')[1].split(' completed')[0]
                    if operation not in operations:
                        operations[operation] = []
                    operations[operation].append(duration)
                except:
                    continue
        
        return {
            "total_operations": len(durations),
            "average_duration": sum(durations) / len(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "operations": {
                op: {
                    "count": len(times),
                    "average": sum(times) / len(times),
                    "max": max(times),
                    "min": min(times)
                }
                for op, times in operations.items()
            }
        }

def setup_advanced_logging(environment: str = None) -> Dict[str, Any]:
    """Setup advanced logging with all features"""
    from config.logging_config import setup_logging, get_config_for_environment
    
    config = get_config_for_environment(environment)
    return setup_logging(**config)
