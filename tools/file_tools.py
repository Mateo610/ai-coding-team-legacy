"""
File system tools for agents to read/write files and navigate directories
"""
import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from tools.code_tools import ToolResult
from agents.timeout_config import TIMEOUT_CONFIG


class FileTools:
    """Tools for file system operations with security restrictions"""
    
    # Security: Only allow operations within project directory
    PROJECT_ROOT = Path.cwd()
    ALLOWED_PATHS = [
        PROJECT_ROOT,
        PROJECT_ROOT / "output",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / ".aiconfig",
    ]
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """
        Check if filepath is safe to access (within allowed directories).
        
        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            # Resolve absolute path
            abs_path = Path(filepath).resolve()
            
            # Check if path is within any allowed directory
            for allowed_path in FileTools.ALLOWED_PATHS:
                allowed_abs = allowed_path.resolve()
                try:
                    abs_path.relative_to(allowed_abs)
                    return True, None
                except ValueError:
                    continue
            
            # Also allow relative paths that don't escape project
            if not abs_path.is_absolute():
                # Check if resolving relative path stays in project
                relative_to_project = (FileTools.PROJECT_ROOT / filepath).resolve()
                try:
                    relative_to_project.relative_to(FileTools.PROJECT_ROOT)
                    return True, None
                except ValueError:
                    pass
            
            return False, f"Path '{filepath}' is outside allowed directories"
        
        except Exception as e:
            return False, f"Invalid path: {str(e)}"
    
    @staticmethod
    def read_file(filepath: str) -> ToolResult:
        """
        Read file contents with error handling.
        
        Security: Only reads files in project directory or subdirectories.
        
        Usage from agent:
        TOOL: read_file
        INPUT: <relative filepath>
        
        Args:
            filepath: Relative path to file from project root
        
        Returns:
            ToolResult with file contents or error
        """
        try:
            # Security check
            is_safe, error_msg = FileTools._is_safe_path(filepath)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg or "Path not allowed",
                    metadata={"filepath": filepath}
                )
            
            # Resolve path relative to project root
            full_path = FileTools.PROJECT_ROOT / filepath
            
            if not full_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"File not found: {filepath}",
                    metadata={"filepath": filepath}
                )
            
            if not full_path.is_file():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path is not a file: {filepath}",
                    metadata={"filepath": filepath}
                )
            
            # Read file
            content = full_path.read_text(encoding='utf-8')
            
            return ToolResult(
                success=True,
                result=content,
                metadata={
                    "filepath": str(full_path),
                    "size": len(content),
                    "lines": len(content.splitlines())
                }
            )
        
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                result=None,
                error=f"File contains binary data (not text): {filepath}",
                metadata={"filepath": filepath}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error reading file: {str(e)}",
                metadata={"filepath": filepath}
            )
    
    @staticmethod
    def write_file(
        filepath: str,
        content: str,
        create_dirs: bool = True
    ) -> ToolResult:
        """
        Write file, creating directories if needed.
        
        Security: Only writes to project directory or subdirectories.
        
        Usage from agent:
        TOOL: write_file
        INPUT: <filepath>\n<content>
        
        Args:
            filepath: Relative path to file from project root
            content: File content to write
            create_dirs: Whether to create parent directories if missing
        
        Returns:
            ToolResult with success status
        """
        try:
            # Security check
            is_safe, error_msg = FileTools._is_safe_path(filepath)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg or "Path not allowed",
                    metadata={"filepath": filepath}
                )
            
            # Resolve path relative to project root
            full_path = FileTools.PROJECT_ROOT / filepath
            
            # Create parent directories if needed
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content, encoding='utf-8')
            
            return ToolResult(
                success=True,
                result=f"File written successfully: {filepath}",
                metadata={
                    "filepath": str(full_path),
                    "size": len(content),
                    "lines": len(content.splitlines())
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error writing file: {str(e)}",
                metadata={"filepath": filepath}
            )
    
    @staticmethod
    def list_directory(path: str = ".") -> ToolResult:
        """
        List files and directories in a directory.
        
        Security: Only lists within project directory.
        
        Usage from agent:
        TOOL: list_directory
        INPUT: <directory path>
        
        Args:
            path: Relative path to directory from project root (default: current directory)
        
        Returns:
            ToolResult with list of files and directories
        """
        try:
            # Security check
            is_safe, error_msg = FileTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg or "Path not allowed",
                    metadata={"path": path}
                )
            
            # Resolve path relative to project root
            full_path = FileTools.PROJECT_ROOT / path
            
            if not full_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Directory not found: {path}",
                    metadata={"path": path}
                )
            
            if not full_path.is_dir():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path is not a directory: {path}",
                    metadata={"path": path}
                )
            
            # List files and directories
            items = []
            try:
                for item in sorted(full_path.iterdir()):
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None
                    })
            except PermissionError:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Permission denied: {path}",
                    metadata={"path": path}
                )
            
            # Format output
            result_lines = [f"Directory: {path}", ""]
            if items:
                result_lines.append("Files and directories:")
                for item in items:
                    type_marker = "📁" if item["type"] == "directory" else "📄"
                    size_info = f" ({item['size']} bytes)" if item["size"] is not None else ""
                    result_lines.append(f"  {type_marker} {item['name']}{size_info}")
            else:
                result_lines.append("(empty directory)")
            
            return ToolResult(
                success=True,
                result="\n".join(result_lines),
                metadata={
                    "path": str(full_path),
                    "items": items,
                    "count": len(items)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error listing directory: {str(e)}",
                metadata={"path": path}
            )
    
    @staticmethod
    def file_exists(filepath: str) -> ToolResult:
        """
        Check if file exists.
        
        Security: Only checks within project directory.
        
        Usage from agent:
        TOOL: file_exists
        INPUT: <filepath>
        
        Args:
            filepath: Relative path to file from project root
        
        Returns:
            ToolResult with existence status
        """
        try:
            # Security check
            is_safe, error_msg = FileTools._is_safe_path(filepath)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg or "Path not allowed",
                    metadata={"filepath": filepath}
                )
            
            # Resolve path relative to project root
            full_path = FileTools.PROJECT_ROOT / filepath
            
            exists = full_path.exists() and full_path.is_file()
            
            return ToolResult(
                success=True,
                result=f"File {'exists' if exists else 'does not exist'}: {filepath}",
                metadata={
                    "filepath": str(full_path),
                    "exists": exists
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error checking file: {str(e)}",
                metadata={"filepath": filepath}
            )
    
    @staticmethod
    def create_directory(path: str) -> ToolResult:
        """
        Create directory structure.
        
        Security: Only creates within project directory.
        
        Usage from agent:
        TOOL: create_directory
        INPUT: <directory path>
        
        Args:
            path: Relative path to directory from project root
        
        Returns:
            ToolResult with success status
        """
        try:
            # Security check
            is_safe, error_msg = FileTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg or "Path not allowed",
                    metadata={"path": path}
                )
            
            # Resolve path relative to project root
            full_path = FileTools.PROJECT_ROOT / path
            
            # Create directory (including parents)
            full_path.mkdir(parents=True, exist_ok=True)
            
            return ToolResult(
                success=True,
                result=f"Directory created (or already exists): {path}",
                metadata={
                    "path": str(full_path),
                    "exists": full_path.exists()
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error creating directory: {str(e)}",
                metadata={"path": path}
            )
    
    @staticmethod
    def find_files(pattern: str, path: str = ".") -> ToolResult:
        """
        Find files matching pattern (glob).
        
        Security: Only searches within project directory.
        
        Usage from agent:
        TOOL: find_files
        INPUT: <pattern> <directory>
        
        Args:
            pattern: Glob pattern (e.g., "*.py", "**/*.md")
            path: Directory to search in (default: current directory)
        
        Returns:
            ToolResult with list of matching files
        """
        try:
            # Security check for path
            is_safe, error_msg = FileTools._is_safe_path(path)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg or "Path not allowed",
                    metadata={"pattern": pattern, "path": path}
                )
            
            # Resolve path relative to project root
            search_path = FileTools.PROJECT_ROOT / path
            
            if not search_path.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Directory not found: {path}",
                    metadata={"pattern": pattern, "path": path}
                )
            
            # Find files matching pattern
            full_pattern = str(search_path / pattern)
            matches = [str(Path(f).relative_to(FileTools.PROJECT_ROOT)) for f in glob.glob(full_pattern, recursive=True)]
            
            # Filter to only files (not directories)
            matches = [m for m in matches if (FileTools.PROJECT_ROOT / m).is_file()]
            
            # Format output
            result_lines = [f"Files matching '{pattern}' in {path}:"]
            if matches:
                for match in sorted(matches):
                    result_lines.append(f"  - {match}")
            else:
                result_lines.append("  (no matches found)")
            
            return ToolResult(
                success=True,
                result="\n".join(result_lines),
                metadata={
                    "pattern": pattern,
                    "path": str(search_path),
                    "matches": matches,
                    "count": len(matches)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error finding files: {str(e)}",
                metadata={"pattern": pattern, "path": str(path)}
            )

