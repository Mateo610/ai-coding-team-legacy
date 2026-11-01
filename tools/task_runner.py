"""
Task Runner tools for agents to run whitelisted commands safely
"""
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from agents.timeout_config import TIMEOUT_CONFIG


class TaskRunnerTools:
    """Tools for running whitelisted tasks/commands safely"""
    
    # Whitelist of allowed commands (security)
    ALLOWED_COMMANDS = {
        "npm": ["run", "install", "test", "build", "dev", "start"],
        "yarn": ["run", "install", "test", "build", "dev", "start"],
        "make": ["migrate", "test", "build", "install", "clean"],
        "alembic": ["upgrade", "downgrade", "revision", "current", "history"],
        "python": ["-m", "pytest", "manage.py"],
        "python3": ["-m", "pytest", "manage.py"],
        "pytest": ["--version", "-v", "--tb=short"],
        "black": ["--version", "--check", "--diff"],
        "flake8": ["--version"],
    }
    
    # Special task patterns (e.g., npm run <script>, make <target>)
    ALLOWED_TASK_PATTERNS = [
        r"^npm run \w+$",
        r"^yarn run \w+$",
        r"^make \w+$",
        r"^alembic upgrade \w+$",
        r"^alembic downgrade \w+$",
        r"^python -m pytest",
        r"^python3 -m pytest",
    ]
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _is_command_allowed(command: str, args: List[str]) -> tuple[bool, Optional[str]]:
        """
        Check if command is in whitelist.
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not command:
            return False, "Command cannot be empty"
        
        # Check if command is in whitelist
        if command not in TaskRunnerTools.ALLOWED_COMMANDS:
            return False, f"Command '{command}' is not in whitelist"
        
        # Check if first argument is allowed
        if args and len(args) > 0:
            first_arg = args[0]
            allowed_args = TaskRunnerTools.ALLOWED_COMMANDS[command]
            
            # Check if first argument matches any allowed pattern
            if not any(
                first_arg == allowed_arg or
                first_arg.startswith(allowed_arg) or
                allowed_arg in first_arg
                for allowed_arg in allowed_args
            ):
                return False, f"Argument '{first_arg}' is not allowed for command '{command}'"
        
        return True, None
    
    @staticmethod
    def _is_task_string_allowed(task_string: str) -> tuple[bool, Optional[str]]:
        """
        Check if task string matches allowed patterns.
        
        Args:
            task_string: Task command string (e.g., "npm run dev")
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Normalize task string
        task_string = task_string.strip()
        
        # Check against patterns
        for pattern in TaskRunnerTools.ALLOWED_TASK_PATTERNS:
            if re.match(pattern, task_string, re.IGNORECASE):
                return True, None
        
        # Try parsing as command + args
        parts = task_string.split()
        if len(parts) > 0:
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            return TaskRunnerTools._is_command_allowed(command, args)
        
        return False, f"Task '{task_string}' does not match any allowed pattern"
    
    @staticmethod
    def run_task(
        command: str,
        args: List[str] = None,
        path: str = ".",
        timeout: int = None
    ) -> ToolResult:
        """
        Run whitelisted task/command safely.
        
        Security: Only allows commands in whitelist.
        
        Args:
            command: Command to run (e.g., "npm", "make", "alembic")
            args: Command arguments (e.g., ["run", "dev"])
            path: Working directory (default: current directory)
            timeout: Timeout in seconds (default: from config)
        
        Returns:
            ToolResult with command output
        """
        try:
            # Validate path
            is_safe, error = TaskRunnerTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "Path is not safe to access"
                )
            
            work_dir = Path(path).resolve()
            if not work_dir.exists() or not work_dir.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid working directory: {path}"
                )
            
            # Normalize command and args
            if args is None:
                args = []
            
            # Check if command is allowed
            is_allowed, error_msg = TaskRunnerTools._is_command_allowed(command, args)
            if not is_allowed:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg or f"Command '{command}' is not allowed"
                )
            
            # Get timeout
            if timeout is None:
                timeout = TIMEOUT_CONFIG.get_code_execution_timeout() * 2  # Longer timeout for tasks
            
            # Build full command
            full_command = [command] + args
            
            # Run command
            try:
                result = subprocess.run(
                    full_command,
                    cwd=str(work_dir),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                return ToolResult(
                    success=result.returncode == 0,
                    result={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                        "command": " ".join(full_command)
                    },
                    error=result.stderr if result.returncode != 0 else "",
                    metadata={
                        "path": str(work_dir),
                        "command": " ".join(full_command),
                        "returncode": result.returncode,
                        "timeout": timeout
                    }
                )
            
            except subprocess.TimeoutExpired:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Command timed out after {timeout}s"
                )
            except FileNotFoundError:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Command '{command}' not found. Is it installed?"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running task: {str(e)}"
            )
    
    @staticmethod
    def list_tasks(path: str = ".") -> ToolResult:
        """
        List available tasks from package.json, Makefile, etc.
        
        Args:
            path: Path to project directory (default: current directory)
        
        Returns:
            ToolResult with available tasks
        """
        try:
            # Validate path
            is_safe, error = TaskRunnerTools._is_safe_path(path)
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
            
            tasks = {
                "npm": [],
                "make": [],
                "alembic": [],
                "other": []
            }
            
            # Check package.json
            package_json = project_path / "package.json"
            if package_json.exists() and package_json.is_file():
                try:
                    with open(package_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        scripts = data.get("scripts", {})
                        tasks["npm"] = list(scripts.keys())
                except Exception:
                    pass
            
            # Check Makefile
            makefile = project_path / "Makefile"
            if makefile.exists() and makefile.is_file():
                try:
                    content = makefile.read_text(encoding='utf-8', errors='ignore')
                    # Extract targets (simple pattern match)
                    target_pattern = r"^([a-zA-Z0-9_-]+):"
                    matches = re.findall(target_pattern, content, re.MULTILINE)
                    # Filter out special targets
                    special_targets = {"all", "clean", "install", "test", "build", "PHONY"}
                    make_targets = [m for m in matches if m.lower() not in special_targets]
                    tasks["make"] = list(set(make_targets))  # Remove duplicates
                except Exception:
                    pass
            
            # Check alembic.ini or migrations directory
            alembic_ini = project_path / "alembic.ini"
            migrations_dir = project_path / "alembic" / "versions"
            if alembic_ini.exists() or (migrations_dir.exists() and migrations_dir.is_dir()):
                tasks["alembic"] = ["upgrade", "downgrade", "revision", "current", "history"]
            
            # Count total tasks
            total_tasks = sum(len(task_list) for task_list in tasks.values())
            
            return ToolResult(
                success=True,
                result={
                    "tasks": tasks,
                    "count": total_tasks
                },
                metadata={
                    "path": str(project_path),
                    "count": total_tasks
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing tasks: {str(e)}"
            )
    
    @staticmethod
    def validate_task(task_string: str) -> ToolResult:
        """
        Validate if task string is allowed.
        
        Args:
            task_string: Task command string (e.g., "npm run dev")
        
        Returns:
            ToolResult with validation result
        """
        try:
            is_allowed, error_msg = TaskRunnerTools._is_task_string_allowed(task_string)
            
            return ToolResult(
                success=is_allowed,
                result={
                    "task": task_string,
                    "allowed": is_allowed
                },
                error=error_msg if not is_allowed else "",
                metadata={
                    "task": task_string,
                    "allowed": is_allowed
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error validating task: {str(e)}"
            )

