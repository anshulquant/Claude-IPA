"""
Advanced Logging Configuration for Claude IPA MVP

This module provides centralized logging configuration with:
- Unicode-safe logging (fixes Windows emoji issues)
- Structured logging with JSON format
- Log rotation and cleanup
- Environment-specific configurations
- Performance monitoring
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Ensure logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class UnicodeSafeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        # Get the formatted message
        message = super().format(record)
        
        # Remove or replace problematic Unicode characters for Windows
        if sys.platform.startswith('win'):
            # Replace common emojis with text equivalents
            emoji_replacements = {
                '🚀': '[START]',
                '✅': '[SUCCESS]',
                '❌': '[ERROR]',
                '⚠️': '[WARNING]',
                '🔄': '[PROCESS]',
                '📸': '[SCREENSHOT]',
                '🧠': '[AI]',
                '🖱️': '[CLICK]',
                '⌨️': '[TYPE]',
                '🌐': '[NAVIGATE]',
                '📊': '[METRICS]',
                '📋': '[REVIEW]',
                '👤': '[HUMAN]',
                '🎉': '[COMPLETE]',
                '🔌': '[CIRCUIT]',
                '⚡': '[STEP]',
                '🛡️': '[PROTECT]',
                '📈': '[PERFORMANCE]',
                '🔍': '[DEBUG]',
                '💾': '[STORAGE]',
                '🌍': '[GLOBAL]'
            }
            
            for emoji, replacement in emoji_replacements.items():
                message = message.replace(emoji, replacement)
        
        return message

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add extra context if present
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        
        # Add performance metrics if present
        if hasattr(record, 'metrics'):
            log_entry["metrics"] = record.metrics
        
        # Add error details if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return str(log_entry)

class PerformanceFilter(logging.Filter):
    """Filter for performance-related log messages"""
    
    def filter(self, record):
        # Add performance context to certain log messages
        if hasattr(record, 'performance'):
            record.context = getattr(record, 'context', {})
            record.context['performance'] = record.performance
        return True

class ErrorTrackingFilter(logging.Filter):
    """Filter for error tracking and categorization"""
    
    def filter(self, record):
        if record.levelno >= logging.ERROR:
            record.context = getattr(record, 'context', {})
            record.context['error_category'] = self._categorize_error(record)
            record.context['error_id'] = f"ERR_{int(datetime.now().timestamp())}"
        return True
    
    def _categorize_error(self, record):
        """Categorize errors based on content"""
        message = record.getMessage().lower()
        
        if 'timeout' in message or 'timed out' in message:
            return 'timeout'
        elif 'network' in message or 'connection' in message:
            return 'network'
        elif 'permission' in message or 'access denied' in message:
            return 'permission'
        elif 'browser' in message or 'selenium' in message:
            return 'browser'
        elif 'claude' in message or 'ai' in message:
            return 'ai'
        elif 'unicode' in message or 'encoding' in message:
            return 'encoding'
        else:
            return 'unknown'

def setup_logging(
    level: str = "INFO",
    environment: str = "development",
    enable_json: bool = False,
    enable_rotation: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_colors: bool = True
) -> Dict[str, Any]:
    """
    Setup advanced logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment (development, production, testing)
        enable_json: Enable JSON structured logging
        enable_rotation: Enable log rotation
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
    
    Returns:
        Dictionary with logging configuration details
    """
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Create formatters
    if enable_json:
        console_formatter = JSONFormatter()
        file_formatter = JSONFormatter()
    elif use_colors:
        # Use colored formatter for console
        from utils.colored_logging import ColoredFormatter
        console_formatter = ColoredFormatter(
            use_colors=True,
            show_emoji=True,
            show_timestamp=True
        )
        file_formatter = UnicodeSafeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    else:
        console_formatter = UnicodeSafeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_formatter = UnicodeSafeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(PerformanceFilter())
    console_handler.addFilter(ErrorTrackingFilter())
    root_logger.addHandler(console_handler)
    
    # File handler
    if enable_rotation:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler(
            LOG_DIR / "app.log",
            encoding='utf-8'
        )
    
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(PerformanceFilter())
    file_handler.addFilter(ErrorTrackingFilter())
    root_logger.addHandler(file_handler)
    
    # Error-specific file handler
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "errors.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    error_handler.addFilter(ErrorTrackingFilter())
    root_logger.addHandler(error_handler)
    
    # Performance metrics handler
    perf_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "performance.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(file_formatter)
    perf_handler.addFilter(PerformanceFilter())
    root_logger.addHandler(perf_handler)
    
    # Configure specific loggers
    _configure_module_loggers(environment)
    
    # Log configuration details
    config_info = {
        "level": level,
        "environment": environment,
        "json_enabled": enable_json,
        "rotation_enabled": enable_rotation,
        "max_file_size": max_file_size,
        "backup_count": backup_count,
        "log_files": {
            "main": str(LOG_DIR / "app.log"),
            "errors": str(LOG_DIR / "errors.log"),
            "performance": str(LOG_DIR / "performance.log")
        }
    }
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized", extra={
        "context": {"config": config_info}
    })
    
    return config_info

def _configure_module_loggers(environment: str):
    """Configure specific module loggers"""
    
    # Workflow executor logger
    workflow_logger = logging.getLogger("core.workflow_executor")
    workflow_logger.setLevel(logging.INFO)
    
    # Review queue logger
    review_logger = logging.getLogger("core.review_queue")
    review_logger.setLevel(logging.INFO)
    
    # API logger
    api_logger = logging.getLogger("api.main")
    api_logger.setLevel(logging.INFO)
    
    # Uvicorn logger (reduce noise)
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.WARNING)
    
    # FastAPI logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with proper configuration"""
    return logging.getLogger(name)

def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    metrics: Optional[Dict[str, Any]] = None
):
    """Log performance metrics"""
    context = {
        "operation": operation,
        "duration": duration,
        "timestamp": datetime.now().isoformat()
    }
    
    if metrics:
        context["metrics"] = metrics
    
    logger.info(f"Performance: {operation} completed in {duration:.3f}s", extra={
        "context": context,
        "performance": True
    })

def log_error_with_context(
    logger: logging.Logger,
    message: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """Log error with additional context"""
    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }
    
    if context:
        error_context.update(context)
    
    logger.error(message, exc_info=True, extra={
        "context": error_context
    })

# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    "level": "DEBUG",
    "environment": "development",
    "enable_json": False,
    "enable_rotation": True,
    "max_file_size": 5 * 1024 * 1024,  # 5MB
    "backup_count": 3
}

PRODUCTION_CONFIG = {
    "level": "INFO",
    "environment": "production",
    "enable_json": True,
    "enable_rotation": True,
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "backup_count": 10
}

TESTING_CONFIG = {
    "level": "WARNING",
    "environment": "testing",
    "enable_json": True,
    "enable_rotation": False,
    "max_file_size": 1024 * 1024,  # 1MB
    "backup_count": 1
}

def get_config_for_environment(environment: str = None) -> Dict[str, Any]:
    """Get logging configuration for specific environment"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    configs = {
        "development": DEVELOPMENT_CONFIG,
        "production": PRODUCTION_CONFIG,
        "testing": TESTING_CONFIG
    }
    
    return configs.get(environment, DEVELOPMENT_CONFIG)
