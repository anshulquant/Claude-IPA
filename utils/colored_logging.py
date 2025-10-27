"""
Enhanced Colored Logging for Quantanite IPA MVP

This module provides:
- Beautiful colored console output
- Rich formatting with emojis and symbols
- Progress indicators and status bars
- Structured log display
- Windows-compatible color support
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

# Color codes for different platforms
class Colors:
    """ANSI color codes for terminal output"""
    
    # Basic colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

class LogLevel(Enum):
    """Log levels with their colors and symbols"""
    DEBUG = {
        'color': Colors.BRIGHT_BLACK,
        'symbol': '🔍',
        'prefix': '[DEBUG]',
        'level': logging.DEBUG
    }
    INFO = {
        'color': Colors.BRIGHT_BLUE,
        'symbol': 'ℹ️',
        'prefix': '[INFO]',
        'level': logging.INFO
    }
    WARNING = {
        'color': Colors.BRIGHT_YELLOW,
        'symbol': '⚠️',
        'prefix': '[WARN]',
        'level': logging.WARNING
    }
    ERROR = {
        'color': Colors.BRIGHT_RED,
        'symbol': '❌',
        'prefix': '[ERROR]',
        'level': logging.ERROR
    }
    CRITICAL = {
        'color': Colors.RED + Colors.BOLD,
        'symbol': '🚨',
        'prefix': '[CRITICAL]',
        'level': logging.CRITICAL
    }

class ColoredFormatter(logging.Formatter):
    """Enhanced formatter with colors and rich formatting"""
    
    def __init__(self, use_colors: bool = True, show_emoji: bool = True, show_timestamp: bool = True):
        self.use_colors = use_colors and self._supports_color()
        self.show_emoji = show_emoji
        self.show_timestamp = show_timestamp
        
        # Format string
        if show_timestamp:
            format_string = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        else:
            format_string = '%(name)s | %(levelname)s | %(message)s'
        
        super().__init__(format_string)
    
    def _supports_color(self) -> bool:
        """Check if terminal supports colors"""
        # Check if we're in a TTY
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check Windows
        if sys.platform.startswith('win'):
            # Enable ANSI escape sequences on Windows 10+
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        
        # Check for color support environment variables
        return os.getenv('TERM') != 'dumb' and os.getenv('NO_COLOR') is None
    
    def format(self, record):
        # Get the base formatted message
        message = super().format(record)
        
        if not self.use_colors:
            return message
        
        # Get log level info
        level_name = record.levelname.upper()
        try:
            level_info = LogLevel[level_name].value
        except KeyError:
            level_info = LogLevel.INFO.value
        
        # Apply colors and formatting
        colored_parts = []
        
        # Timestamp
        if self.show_timestamp:
            timestamp = message.split(' | ')[0]
            colored_parts.append(f"{Colors.DIM}{timestamp}{Colors.RESET}")
            message = ' | '.join(message.split(' | ')[1:])
        
        # Logger name
        parts = message.split(' | ')
        if len(parts) >= 3:
            logger_name = parts[0]
            level_name = parts[1]
            log_message = ' | '.join(parts[2:])
            
            # Color logger name
            colored_logger = f"{Colors.CYAN}{logger_name}{Colors.RESET}"
            colored_parts.append(colored_logger)
            
            # Color level with emoji
            if self.show_emoji:
                colored_level = f"{level_info['color']}{level_info['symbol']} {level_info['prefix']}{Colors.RESET}"
            else:
                colored_level = f"{level_info['color']}{level_info['prefix']}{Colors.RESET}"
            colored_parts.append(colored_level)
            
            # Color message
            colored_message = self._colorize_message(log_message, level_info)
            colored_parts.append(colored_message)
            
            return ' | '.join(colored_parts)
        
        return message
    
    def _colorize_message(self, message: str, level_info: LogLevel) -> str:
        """Apply specific coloring to message content"""
        # Highlight important patterns
        patterns = [
            # Performance metrics
            (r'(\d+\.\d+)s', f"{Colors.BRIGHT_GREEN}\\1s{Colors.RESET}"),
            (r'(\d+)ms', f"{Colors.BRIGHT_GREEN}\\1ms{Colors.RESET}"),
            (r'(\d+)%', f"{Colors.BRIGHT_YELLOW}\\1%{Colors.RESET}"),
            
            # Status indicators
            (r'\b(success|completed|done|finished)\b', f"{Colors.BRIGHT_GREEN}\\1{Colors.RESET}"),
            (r'\b(error|failed|exception|timeout)\b', f"{Colors.BRIGHT_RED}\\1{Colors.RESET}"),
            (r'\b(warning|warn|caution)\b', f"{Colors.BRIGHT_YELLOW}\\1{Colors.RESET}"),
            (r'\b(info|information|note)\b', f"{Colors.BRIGHT_BLUE}\\1{Colors.RESET}"),
            
            # Action types
            (r'\b(click|typing|navigate|scroll|wait)\b', f"{Colors.BRIGHT_CYAN}\\1{Colors.RESET}"),
            (r'\b(screenshot|capture|image)\b', f"{Colors.BRIGHT_MAGENTA}\\1{Colors.RESET}"),
            (r'\b(ai|claude|decision|analysis)\b', f"{Colors.BRIGHT_BLUE}\\1{Colors.RESET}"),
            
            # URLs and paths
            (r'(https?://[^\s]+)', f"{Colors.UNDERLINE}{Colors.BLUE}\\1{Colors.RESET}"),
            (r'([A-Za-z]:\\[^\s]+)', f"{Colors.UNDERLINE}{Colors.BLUE}\\1{Colors.RESET}"),
            (r'(/[^\s]+)', f"{Colors.UNDERLINE}{Colors.BLUE}\\1{Colors.RESET}"),
            
            # Numbers and IDs
            (r'\b(\d+)\b', f"{Colors.BRIGHT_WHITE}\\1{Colors.RESET}"),
            (r'\b([A-Z]{2,}_\d+)\b', f"{Colors.BRIGHT_MAGENTA}\\1{Colors.RESET}"),  # Error IDs
        ]
        
        import re
        for pattern, replacement in patterns:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        return message

class ProgressBar:
    """Simple progress bar for console output"""
    
    def __init__(self, total: int, width: int = 50, show_percentage: bool = True):
        self.total = total
        self.width = width
        self.show_percentage = show_percentage
        self.current = 0
        self.start_time = time.time()
    
    def update(self, current: int, message: str = ""):
        """Update progress bar"""
        self.current = min(current, self.total)
        progress = self.current / self.total
        filled = int(self.width * progress)
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Calculate ETA
        if self.current > 0:
            elapsed = time.time() - self.start_time
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: --"
        
        # Build progress string
        progress_str = f"\r{Colors.BRIGHT_BLUE}[{bar}]{Colors.RESET}"
        
        if self.show_percentage:
            percentage = progress * 100
            progress_str += f" {Colors.BRIGHT_WHITE}{percentage:5.1f}%{Colors.RESET}"
        
        progress_str += f" {Colors.DIM}({self.current}/{self.total}){Colors.RESET}"
        progress_str += f" {Colors.BRIGHT_CYAN}{eta_str}{Colors.RESET}"
        
        if message:
            progress_str += f" {Colors.BRIGHT_GREEN}{message}{Colors.RESET}"
        
        sys.stdout.write(progress_str)
        sys.stdout.flush()
    
    def finish(self, message: str = "Complete!"):
        """Finish progress bar"""
        self.update(self.total, message)
        print()  # New line

class StatusIndicator:
    """Status indicator for ongoing operations"""
    
    def __init__(self, message: str = "Processing..."):
        self.message = message
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_char = 0
        self.running = False
    
    def start(self):
        """Start the spinner"""
        self.running = True
        self._spin()
    
    def stop(self, message: str = "Done!"):
        """Stop the spinner"""
        self.running = False
        print(f"\r{Colors.BRIGHT_GREEN}✓{Colors.RESET} {message}")
    
    def _spin(self):
        """Spin the spinner"""
        if not self.running:
            return
        
        char = self.spinner_chars[self.current_char]
        print(f"\r{Colors.BRIGHT_CYAN}{char}{Colors.RESET} {self.message}", end="", flush=True)
        
        self.current_char = (self.current_char + 1) % len(self.spinner_chars)
        
        # Schedule next spin
        import threading
        threading.Timer(0.1, self._spin).start()

def setup_colored_logging(
    level: str = "INFO",
    show_emoji: bool = True,
    show_timestamp: bool = True,
    use_colors: bool = True
) -> logging.Logger:
    """
    Setup colored logging for the application
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        show_emoji: Show emojis in log output
        show_timestamp: Show timestamps in log output
        use_colors: Enable colored output
    
    Returns:
        Configured logger
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Create colored formatter
    formatter = ColoredFormatter(
        use_colors=use_colors,
        show_emoji=show_emoji,
        show_timestamp=show_timestamp
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (no colors for file)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import os
    os.makedirs('logs', exist_ok=True)
    
    file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    return root_logger

def log_workflow_progress(
    logger: logging.Logger,
    step: int,
    total_steps: int,
    action: str,
    status: str,
    details: str = ""
):
    """Log workflow progress with visual indicators"""
    progress = (step / total_steps) * 100
    
    # Create progress bar
    bar_width = 20
    filled = int(bar_width * (step / total_steps))
    bar = '█' * filled + '░' * (bar_width - filled)
    
    # Status color
    if status.lower() in ['success', 'completed', 'done']:
        status_color = Colors.BRIGHT_GREEN
        status_symbol = '✓'
    elif status.lower() in ['error', 'failed', 'exception']:
        status_color = Colors.BRIGHT_RED
        status_symbol = '✗'
    elif status.lower() in ['warning', 'warn']:
        status_color = Colors.BRIGHT_YELLOW
        status_symbol = '⚠'
    else:
        status_color = Colors.BRIGHT_BLUE
        status_symbol = 'ℹ'
    
    # Format message
    message = (
        f"{Colors.BRIGHT_CYAN}[{bar}]{Colors.RESET} "
        f"{Colors.BRIGHT_WHITE}{progress:5.1f}%{Colors.RESET} "
        f"{Colors.DIM}({step}/{total_steps}){Colors.RESET} "
        f"{status_color}{status_symbol} {action}{Colors.RESET}"
    )
    
    if details:
        message += f" {Colors.DIM}- {details}{Colors.RESET}"
    
    logger.info(message)

def log_performance_metrics(
    logger: logging.Logger,
    operation: str,
    duration: float,
    memory_usage: float = None,
    additional_metrics: Dict[str, Any] = None
):
    """Log performance metrics with visual formatting"""
    # Duration color based on performance
    if duration < 1.0:
        duration_color = Colors.BRIGHT_GREEN
    elif duration < 5.0:
        duration_color = Colors.BRIGHT_YELLOW
    else:
        duration_color = Colors.BRIGHT_RED
    
    # Format message
    message = (
        f"{Colors.BRIGHT_MAGENTA}📊 Performance{Colors.RESET} "
        f"{Colors.BRIGHT_CYAN}{operation}{Colors.RESET} "
        f"completed in {duration_color}{duration:.3f}s{Colors.RESET}"
    )
    
    if memory_usage:
        memory_color = Colors.BRIGHT_GREEN if memory_usage < 100 else Colors.BRIGHT_YELLOW
        message += f" | Memory: {memory_color}{memory_usage:.1f}MB{Colors.RESET}"
    
    if additional_metrics:
        for key, value in additional_metrics.items():
            message += f" | {Colors.BRIGHT_WHITE}{key}{Colors.RESET}: {Colors.BRIGHT_CYAN}{value}{Colors.RESET}"
    
    logger.info(message)

# Example usage and testing
if __name__ == "__main__":
    # Setup colored logging
    logger = setup_colored_logging(level="DEBUG")
    
    # Test different log levels
    logger.debug("This is a debug message with detailed information")
    logger.info("Application started successfully")
    logger.warning("This is a warning message about potential issues")
    logger.error("An error occurred during execution")
    logger.critical("Critical system failure detected")
    
    # Test progress logging
    log_workflow_progress(logger, 3, 10, "Clicking search button", "success", "Element found and clicked")
    
    # Test performance logging
    log_performance_metrics(logger, "Workflow execution", 2.5, 45.2, {"steps": 10, "retries": 1})
    
    # Test progress bar
    print("\nTesting progress bar:")
    progress = ProgressBar(100, width=30)
    for i in range(101):
        progress.update(i, f"Processing item {i}")
        time.sleep(0.05)
    progress.finish("All items processed!")
    
    # Test status indicator
    print("\nTesting status indicator:")
    spinner = StatusIndicator("Processing workflow...")
    spinner.start()
    time.sleep(3)
    spinner.stop("Workflow completed successfully!")
