"""
Consolidated File System Tools
Replaces: read_file, file_exists, write_file, save_file, create_directory, list_directory, find_files, list_logs
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from tools.log_reader import LogReaderTools


class FSTools:
    """Consolidated file system tools with mode-based operations"""
    
    @staticmethod
    def fs_read(file_path: str, mode: str = "read") -> ToolResult:
        """
        Read file content or check existence.
        
        Replaces: read_file, file_exists
        
        Args:
            file_path: Path to file (relative or absolute)
            mode: Operation mode - "read" (default) or "exists"
        
        Returns:
            ToolResult with file content (mode="read") or existence status (mode="exists")
        
        Examples:
            fs_read("src/main.py", mode="read")  # Read file content
            fs_read("src/main.py", mode="exists")  # Check if file exists
        """
        try:
            if mode == "read":
                # Use FileTools.read_file
                result = FileTools.read_file(file_path)
                return result
            elif mode == "exists":
                # Use FileTools.file_exists
                result = FileTools.file_exists(file_path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'read', 'exists'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in fs_read with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def fs_write(file_path: str, content: str = None, mode: str = "write") -> ToolResult:
        """
        Write files or create directories safely.
        
        Replaces: write_file, save_file, create_directory
        
        Args:
            file_path: Path to file or directory
            content: File content (required for mode="write" or "save")
            mode: Operation mode - "write" (default), "save", or "directory"
        
        Returns:
            ToolResult with operation result
        
        Examples:
            fs_write("src/main.py", content="# Code here", mode="write")  # Write file
            fs_write("src/main.py", content="# Code here", mode="save")  # Save file (alias)
            fs_write("src/", mode="directory")  # Create directory
        """
        try:
            if mode == "write" or mode == "save":
                # Use FileTools.write_file for both write and save
                if content is None:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Content required for mode '{mode}'"
                    )
                result = FileTools.write_file(file_path, content)
                return result
            elif mode == "directory":
                # Use FileTools.create_directory
                result = FileTools.create_directory(file_path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'write', 'save', 'directory'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in fs_write with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def fs_list(path: str = ".", mode: str = "directory", pattern: str = None) -> ToolResult:
        """
        Enumerate directories, search for patterns, list logs.
        
        Replaces: list_directory, find_files, list_logs
        
        Args:
            path: Directory path (default: current directory)
            mode: Operation mode - "directory" (default), "files", or "logs"
            pattern: Search pattern for file matching (required for mode="files")
        
        Returns:
            ToolResult with directory listing, file search results, or log files list
        
        Examples:
            fs_list("src/", mode="directory")  # List directory contents
            fs_list("src/", mode="files", pattern="*.py")  # Find files matching pattern
            fs_list("logs/", mode="logs")  # List log files
        """
        try:
            if mode == "directory":
                # Use FileTools.list_directory
                result = FileTools.list_directory(path)
                return result
            elif mode == "files":
                # Use FileTools.find_files
                if pattern is None:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="Pattern required for mode='files'"
                    )
                result = FileTools.find_files(pattern, path=path)
                return result
            elif mode == "logs":
                # Use LogReaderTools.list_logs
                result = LogReaderTools.list_logs(log_dir=path if path != "." else None)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'directory', 'files', 'logs'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in fs_list with mode '{mode}': {str(e)}"
            )

