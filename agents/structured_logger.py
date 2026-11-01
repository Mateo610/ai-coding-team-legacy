"""
Structured logging system for the AI software team.
Provides log levels, structured format (JSON), filtering, and rotation.
"""

import os
import json
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from agents.config_manager import CONFIG_MANAGER
from agents.exceptions import ConfigurationError


class LogLevel(Enum):
    """Log levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    logger: str
    message: str
    component: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Extract exception information if present
        exc_info = None
        stack_trace = None
        if record.exc_info:
            exc_info = self.formatException(record.exc_info)
            stack_trace = exc_info
        
        # Get component from extra if available
        component = getattr(record, 'component', None)
        
        # Create structured log entry
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            component=component,
            details=getattr(record, 'details', {}),
            error=str(record.exc_info[1]) if record.exc_info else None,
            stack_trace=stack_trace
        )
        
        return json.dumps(log_entry.to_dict(), default=str)


class StructuredLogger:
    """
    Structured logging system with levels, filtering, and rotation.
    """
    
    DEFAULT_LOG_DIR = "~/ai-coding-team/logs"
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    DEFAULT_BACKUP_COUNT = 5
    
    def __init__(self, 
                 name: str = "ai_team",
                 log_dir: Optional[str] = None,
                 log_level: Optional[str] = None,
                 console_output: bool = True,
                 json_format: bool = True):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            log_dir: Log directory (default: from config or ~/ai-coding-team/logs)
            log_level: Log level (default: from config or INFO)
            console_output: Whether to output to console
            json_format: Whether to use JSON format (default: True)
        """
        self.name = name
        self.config_manager = CONFIG_MANAGER
        
        # Get configuration
        self.log_dir = Path(log_dir or self.config_manager.get_env_var("LOG_DIR") or self.DEFAULT_LOG_DIR).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_level = log_level or self.config_manager.get_log_level() or self.DEFAULT_LOG_LEVEL
        self.console_output = console_output
        self.json_format = json_format
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.log_level.upper(), logging.INFO))
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Create formatter
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Add file handler with rotation
        self._setup_file_handler(formatter)
        
        # Add console handler if requested
        if console_output:
            self._setup_console_handler(formatter)
    
    def _setup_file_handler(self, formatter: logging.Formatter) -> None:
        """Setup rotating file handler"""
        log_file = self.log_dir / f"{self.name}.log"
        
        # Create rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.DEFAULT_MAX_BYTES,
            backupCount=self.DEFAULT_BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        handler.setLevel(self.logger.level)
        self.logger.addHandler(handler)
        
        self.file_handler = handler
    
    def _setup_console_handler(self, formatter: logging.Formatter) -> None:
        """Setup console handler"""
        # Use simpler format for console
        if self.json_format:
            # For JSON, use compact format
            console_formatter = logging.Formatter(
                '%(levelname)s: %(message)s'
            )
        else:
            console_formatter = formatter
        
        handler = logging.StreamHandler()
        handler.setFormatter(console_formatter)
        handler.setLevel(self.logger.level)
        self.logger.addHandler(handler)
    
    def debug(self, message: str, component: str = None, details: Dict[str, Any] = None) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, component, details)
    
    def info(self, message: str, component: str = None, details: Dict[str, Any] = None) -> None:
        """Log info message"""
        self._log(logging.INFO, message, component, details)
    
    def warning(self, message: str, component: str = None, details: Dict[str, Any] = None) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, component, details)
    
    def error(self, message: str, component: str = None, details: Dict[str, Any] = None, exc_info: bool = False) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, component, details, exc_info=exc_info)
    
    def critical(self, message: str, component: str = None, details: Dict[str, Any] = None, exc_info: bool = False) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, component, details, exc_info=exc_info)
    
    def _log(self, level: int, message: str, component: str = None, details: Dict[str, Any] = None, exc_info: bool = False) -> None:
        """Internal log method"""
        extra = {}
        if component:
            extra['component'] = component
        if details:
            extra['details'] = details
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info if exc_info else None)
    
    def log_operation(self, operation: str, component: str, details: Dict[str, Any] = None) -> None:
        """Log operation start"""
        self.info(f"Starting {operation}", component=component, details=details or {})
    
    def log_operation_result(self, operation: str, component: str, success: bool, details: Dict[str, Any] = None) -> None:
        """Log operation result"""
        status = "completed" if success else "failed"
        level = logging.INFO if success else logging.ERROR
        message = f"{operation} {status}"
        
        result_details = details or {}
        result_details['success'] = success
        
        self._log(level, message, component=component, details=result_details)
    
    def log_performance(self, operation: str, component: str, duration_ms: int, details: Dict[str, Any] = None) -> None:
        """Log performance metrics"""
        perf_details = details or {}
        perf_details['duration_ms'] = duration_ms
        
        # Log as info with performance details
        self.info(f"{operation} completed", component=component, details=perf_details)
    
    def set_level(self, level: str) -> None:
        """Set log level"""
        level_num = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(level_num)
        for handler in self.logger.handlers:
            handler.setLevel(level_num)
    
    def get_log_files(self) -> list[Path]:
        """Get all log files for this logger"""
        log_files = []
        base_file = self.log_dir / f"{self.name}.log"
        
        # Main log file
        if base_file.exists():
            log_files.append(base_file)
        
        # Rotated log files
        for i in range(1, self.DEFAULT_BACKUP_COUNT + 1):
            rotated_file = self.log_dir / f"{self.name}.log.{i}"
            if rotated_file.exists():
                log_files.append(rotated_file)
        
        return log_files
    
    def archive_logs(self, archive_dir: Optional[str] = None) -> None:
        """
        Archive old log files.
        
        Args:
            archive_dir: Archive directory (default: logs/archive)
        """
        if archive_dir is None:
            archive_dir = self.log_dir / "archive"
        else:
            archive_dir = Path(archive_dir).expanduser()
        
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        log_files = self.get_log_files()
        archived_count = 0
        
        for log_file in log_files:
            if log_file.stat().st_size > 0:  # Only archive non-empty files
                archive_path = archive_dir / f"{log_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{log_file.suffix}"
                log_file.rename(archive_path)
                archived_count += 1
        
        if archived_count > 0:
            self.info(f"Archived {archived_count} log files", component="logger", details={"archive_dir": str(archive_dir)})
    
    def get_recent_logs(self, lines: int = 100) -> list[Dict[str, Any]]:
        """
        Get recent log entries.
        
        Args:
            lines: Number of lines to read
        
        Returns:
            List of log entries as dictionaries
        """
        log_file = self.log_dir / f"{self.name}.log"
        
        if not log_file.exists():
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # Read last N lines
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        if self.json_format:
                            entry = json.loads(line)
                        else:
                            # Parse standard format
                            entry = self._parse_standard_log(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
        except Exception as e:
            self.error(f"Failed to read log file: {str(e)}", component="logger")
        
        return entries
    
    def _parse_standard_log(self, line: str) -> Dict[str, Any]:
        """Parse standard log format"""
        # Simple parser for standard format
        # Format: timestamp - name - level - message
        parts = line.split(' - ', 3)
        if len(parts) >= 4:
            return {
                "timestamp": parts[0],
                "logger": parts[1],
                "level": parts[2],
                "message": parts[3]
            }
        return {"message": line}


# Create singleton logger
STRUCTURED_LOGGER = StructuredLogger(name="ai_team")

