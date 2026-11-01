"""
Consolidated Runtime Infrastructure Tools
Replaces: run_task, list_tasks, validate_task, docker_ps, docker_compose_ps, docker_status, docker_health, docker_logs, read_log, tail_log, search_log, filter_log
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.task_runner import TaskRunnerTools
from tools.docker_tools import DockerTools
from tools.log_reader import LogReaderTools


class RuntimeTools:
    """Consolidated runtime infrastructure tools with mode-based operations"""
    
    @staticmethod
    def task_run(task: str, path: str = ".", mode: str = "run") -> ToolResult:
        """
        Unified task runner (npm, make, poetry, alembic).
        
        Replaces: run_task, list_tasks, validate_task
        
        Args:
            task: Task command (e.g., "npm run dev", "make migrate")
            path: Project path (default: current directory)
            mode: Operation mode:
                - "run" (default): Execute task
                - "list": List available tasks
                - "validate": Validate task before execution
        
        Returns:
            ToolResult with task execution result based on mode
        
        Examples:
            task_run("npm run dev", mode="run")  # Run task
            task_run("npm run", mode="list")  # List available tasks
            task_run("npm run dev", mode="validate")  # Validate task
        """
        try:
            if mode == "run":
                # Use TaskRunnerTools.run_task
                result = TaskRunnerTools.run_task(task, path=path)
                return result
            elif mode == "list":
                # Use TaskRunnerTools.list_tasks
                result = TaskRunnerTools.list_tasks(task, path=path)
                return result
            elif mode == "validate":
                # Use TaskRunnerTools.validate_task
                result = TaskRunnerTools.validate_task(task, path=path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'run', 'list', 'validate'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in task_run with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def docker_inspect(mode: str = "ps", container_name: str = None, compose_file: str = "docker-compose.yml", path: str = ".") -> ToolResult:
        """
        Inspect local Docker state/services.
        
        Replaces: docker_ps, docker_compose_ps, docker_status, docker_health
        
        Args:
            mode: Operation mode:
                - "ps" (default): List running containers
                - "compose": List docker-compose services
                - "status": Get container status
                - "health": Check container health
            container_name: Container name (required for status/health modes)
            compose_file: Docker compose file (default: "docker-compose.yml")
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with Docker information based on mode
        
        Examples:
            docker_inspect(mode="ps")  # List containers
            docker_inspect(mode="compose")  # List compose services
            docker_inspect(mode="status", container_name="app")  # Get container status
            docker_inspect(mode="health", container_name="app")  # Check container health
        """
        try:
            if mode == "ps":
                # Use DockerTools.docker_ps
                result = DockerTools.docker_ps(path=path)
                return result
            elif mode == "compose":
                # Use DockerTools.docker_compose_ps
                result = DockerTools.docker_compose_ps(compose_file=compose_file, path=path)
                return result
            elif mode == "status":
                # Use DockerTools.docker_status
                if not container_name:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="container_name required for mode='status'"
                    )
                result = DockerTools.docker_status(container_name, path=path)
                return result
            elif mode == "health":
                # Use DockerTools.docker_health
                if not container_name:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="container_name required for mode='health'"
                    )
                result = DockerTools.docker_health(container_name, path=path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'ps', 'compose', 'status', 'health'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in docker_inspect with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def docker_logs(container_name: str, lines: int = 50, path: str = ".") -> ToolResult:
        """
        Get logs from containers.
        
        Replaces: docker_logs
        
        Args:
            container_name: Container name or ID
            lines: Number of lines to get (default: 50)
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with container logs
        
        Examples:
            docker_logs("app", lines=100)  # Get last 100 lines
        """
        try:
            # Use DockerTools.docker_logs
            result = DockerTools.docker_logs(container_name, lines=lines, path=path)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in docker_logs: {str(e)}"
            )
    
    @staticmethod
    def log_inspect(log_path: str, mode: str = "read", lines: int = 100, keyword: str = None, level: str = None, path: str = ".") -> ToolResult:
        """
        Inspect, search, filter log files.
        
        Replaces: read_log, tail_log, search_log, filter_log
        
        Args:
            log_path: Path to log file
            mode: Operation mode:
                - "read" (default): Read log file
                - "tail": Get last N lines
                - "search": Search logs by keyword
                - "filter": Filter logs by level/keyword
            lines: Number of lines to read (default: 100)
            keyword: Keyword to search for (optional, for search/filter modes)
            level: Log level to filter (optional, for filter mode)
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with log entries based on mode
        
        Examples:
            log_inspect("logs/app.log", mode="read")  # Read log file
            log_inspect("logs/app.log", mode="tail", lines=50)  # Tail log
            log_inspect("logs/app.log", mode="search", keyword="error")  # Search logs
            log_inspect("logs/app.log", mode="filter", level="ERROR")  # Filter by level
        """
        try:
            if mode == "read":
                # Use LogReaderTools.read_log
                result = LogReaderTools.read_log(log_path, lines=lines, path=path)
                return result
            elif mode == "tail":
                # Use LogReaderTools.tail_log
                result = LogReaderTools.tail_log(log_path, lines=lines, path=path)
                return result
            elif mode == "search":
                # Use LogReaderTools.search_log
                if not keyword:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="keyword required for mode='search'"
                    )
                result = LogReaderTools.search_log(log_path, keyword=keyword, lines=lines, path=path)
                return result
            elif mode == "filter":
                # Use LogReaderTools.filter_log
                result = LogReaderTools.filter_log(log_path, level=level, keyword=keyword, lines=lines, path=path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'read', 'tail', 'search', 'filter'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in log_inspect with mode '{mode}': {str(e)}"
            )

