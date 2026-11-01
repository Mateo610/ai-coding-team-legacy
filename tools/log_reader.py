"""
Log Reader tools for agents to read and filter application logs
"""
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from tools.code_tools import ToolResult
from tools.file_tools import FileTools


class LogReaderTools:
    """Tools for reading and filtering logs"""
    
    # Common log file patterns
    LOG_FILE_PATTERNS = [
        "*.log",
        "logs/*.log",
        "log/*.log",
        "*.log.*",  # Rotated logs
    ]
    
    # Log level patterns
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _parse_log_line(line: str) -> Dict[str, Any]:
        """Parse a log line to extract level, timestamp, message"""
        log_info = {
            "level": None,
            "timestamp": None,
            "message": line.strip()
        }
        
        # Try to extract log level
        for level in LogReaderTools.LOG_LEVELS:
            if re.search(rf'\b{level}\b', line, re.IGNORECASE):
                log_info["level"] = level.upper()
                break
        
        # Try to extract timestamp (common formats)
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',  # 2024-01-01 12:00:00
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',    # 2024-01-01T12:00:00
            r'\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\]',  # [2024-01-01 12:00:00]
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp_str = match.group(0).strip('[]')
                    log_info["timestamp"] = timestamp_str
                except:
                    pass
                break
        
        return log_info
    
    @staticmethod
    def read_log(
        log_path: str,
        lines: int = 100,
        keyword: str = None,
        level: str = None,
        time_range: tuple = None,
        path: str = "."
    ) -> ToolResult:
        """
        Read log file with optional filtering.
        
        Args:
            log_path: Path to log file
            lines: Number of lines to read (default: 100)
            keyword: Filter by keyword (optional)
            level: Filter by log level (optional)
            time_range: Filter by time range (optional, tuple of (start, end))
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with filtered log entries
        """
        try:
            # Validate path
            is_safe, error = LogReaderTools._is_safe_path(log_path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Log path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            file_path = (project_path / log_path).resolve()
            
            if not file_path.exists() or not file_path.is_file():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Log file not found: {log_path}"
                )
            
            # Read file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
            except Exception as e:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Error reading log file: {str(e)}"
                )
            
            # Take last N lines
            log_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            # Filter logs
            filtered_lines = []
            for line in log_lines:
                # Parse log line
                log_info = LogReaderTools._parse_log_line(line)
                
                # Apply filters
                include = True
                
                # Keyword filter
                if keyword and keyword.lower() not in line.lower():
                    include = False
                
                # Level filter
                if level and log_info["level"]:
                    if level.upper() != log_info["level"]:
                        include = False
                elif level and not log_info["level"]:
                    # If level filter specified but no level found in line, exclude
                    include = False
                
                # Time range filter (simplified - would need proper date parsing)
                if time_range and log_info["timestamp"]:
                    # This is a simplified version - full implementation would parse dates
                    pass
                
                if include:
                    filtered_lines.append({
                        "line": line.strip(),
                        "level": log_info["level"],
                        "timestamp": log_info["timestamp"],
                        "message": log_info["message"]
                    })
            
            return ToolResult(
                success=True,
                result={
                    "entries": filtered_lines,
                    "count": len(filtered_lines),
                    "total_lines": len(all_lines)
                },
                metadata={
                    "path": str(project_path),
                    "log_path": log_path,
                    "filtered_count": len(filtered_lines),
                    "total_count": len(all_lines)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error reading log: {str(e)}"
            )
    
    @staticmethod
    def tail_log(log_path: str, lines: int = 50, path: str = ".") -> ToolResult:
        """
        Get last N lines of log file.
        
        Args:
            log_path: Path to log file
            lines: Number of lines to get (default: 50)
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with last N lines
        """
        return LogReaderTools.read_log(log_path, lines=lines, path=path)
    
    @staticmethod
    def search_log(
        log_path: str,
        keyword: str,
        path: str = ".",
        lines: int = None
    ) -> ToolResult:
        """
        Search logs by keyword.
        
        Args:
            log_path: Path to log file
            keyword: Keyword to search for
            path: Project path (default: current directory)
            lines: Maximum lines to search (default: all)
        
        Returns:
            ToolResult with matching log entries
        """
        # Read all lines if not specified
        max_lines = lines if lines else 10000  # Large number to read all
        
        return LogReaderTools.read_log(log_path, lines=max_lines, keyword=keyword, path=path)
    
    @staticmethod
    def filter_log(
        log_path: str,
        level: str = None,
        keyword: str = None,
        time_range: tuple = None,
        path: str = ".",
        lines: int = 100
    ) -> ToolResult:
        """
        Filter logs by time range or level.
        
        Args:
            log_path: Path to log file
            level: Filter by log level (optional)
            keyword: Filter by keyword (optional)
            time_range: Filter by time range (optional)
            path: Project path (default: current directory)
            lines: Number of lines to read (default: 100)
        
        Returns:
            ToolResult with filtered log entries
        """
        return LogReaderTools.read_log(
            log_path,
            lines=lines,
            keyword=keyword,
            level=level,
            time_range=time_range,
            path=path
        )
    
    @staticmethod
    def list_logs(path: str = ".") -> ToolResult:
        """
        List available log files.
        
        Args:
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with list of log files
        """
        try:
            # Validate path
            is_safe, error = LogReaderTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            if not project_path.exists() or not project_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid project path: {path}"
                )
            
            # Find log files
            log_files = []
            
            # Check common log locations
            log_dirs = ["logs", "log", "."]
            for log_dir in log_dirs:
                log_path = project_path / log_dir
                if log_path.exists():
                    # Find .log files
                    for pattern in ["*.log", "*.log.*"]:
                        for log_file in log_path.glob(pattern):
                            if log_file.is_file():
                                log_info = {
                                    "file": str(log_file.relative_to(project_path)),
                                    "path": str(log_file),
                                    "size": log_file.stat().st_size
                                }
                                log_files.append(log_info)
            
            # Also check root for .log files
            for pattern in ["*.log", "*.log.*"]:
                for log_file in project_path.glob(pattern):
                    if log_file.is_file():
                        log_info = {
                            "file": str(log_file.relative_to(project_path)),
                            "path": str(log_file),
                            "size": log_file.stat().st_size
                        }
                        # Avoid duplicates
                        if not any(lf["file"] == log_info["file"] for lf in log_files):
                            log_files.append(log_info)
            
            return ToolResult(
                success=True,
                result={
                    "log_files": log_files,
                    "count": len(log_files)
                },
                metadata={
                    "path": str(project_path),
                    "count": len(log_files)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing logs: {str(e)}"
            )

