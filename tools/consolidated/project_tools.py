"""
Consolidated Project & Code Search Tools
Replaces: scan_project, find_entrypoints, list_configs, find_tests, find_env_files, search_code, find_usages, find_definitions, find_todos, find_imports
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.project_scanner import ProjectScanner
from tools.code_search import CodeSearchTools


class ProjectTools:
    """Consolidated project scanning and code search tools with mode-based operations"""
    
    @staticmethod
    def project_scan(project_path: str = ".", mode: str = "full") -> ToolResult:
        """
        Detect project structure, configs, test suites, env files.
        
        Replaces: scan_project, find_entrypoints, list_configs, find_tests, find_env_files
        
        Args:
            project_path: Path to project root (default: current directory)
            mode: Operation mode:
                - "full" (default): Complete project scan
                - "entrypoints": Find project entry points
                - "configs": List configuration files
                - "tests": Find test files
                - "env": Find environment files
        
        Returns:
            ToolResult with project structure information based on mode
        
        Examples:
            project_scan(".", mode="full")  # Complete project scan
            project_scan(".", mode="entrypoints")  # Find entry points
            project_scan(".", mode="configs")  # List config files
            project_scan(".", mode="tests")  # Find test files
            project_scan(".", mode="env")  # Find env files
        """
        try:
            if mode == "full":
                # Use ProjectScanner.scan_project
                result = ProjectScanner.scan_project(path=project_path)
                return result
            elif mode == "entrypoints":
                # Use ProjectScanner.find_entrypoints
                result = ProjectScanner.find_entrypoints(path=project_path)
                return result
            elif mode == "configs":
                # Use ProjectScanner.list_configs
                result = ProjectScanner.list_configs(path=project_path)
                return result
            elif mode == "tests":
                # Use ProjectScanner.find_tests
                result = ProjectScanner.find_tests(path=project_path)
                return result
            elif mode == "env":
                # Use ProjectScanner.find_env_files
                result = ProjectScanner.find_env_files(path=project_path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'full', 'entrypoints', 'configs', 'tests', 'env'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in project_scan with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def code_search(pattern: str, search_path: str = ".", mode: str = "text") -> ToolResult:
        """
        Search codebase by text, symbols, TODOs, imports.
        
        Replaces: search_code, find_usages, find_definitions, find_todos, find_imports
        
        Args:
            pattern: Search pattern (text, symbol name, etc.)
            search_path: Path to search in (default: current directory)
            mode: Operation mode:
                - "text" (default): Text/regex search
                - "usages": Find usages of symbol
                - "definitions": Find definitions of symbol
                - "todos": Find TODO comments
                - "imports": Find import statements
        
        Returns:
            ToolResult with search results based on mode
        
        Examples:
            code_search("def main", mode="text")  # Text search
            code_search("MyClass", mode="usages")  # Find usages
            code_search("MyClass", mode="definitions")  # Find definition
            code_search("TODO", mode="todos")  # Find TODOs
            code_search("flask", mode="imports")  # Find imports
        """
        try:
            if mode == "text":
                # Use CodeSearchTools.search_code
                result = CodeSearchTools.search_code(pattern, search_path=search_path)
                return result
            elif mode == "usages":
                # Use CodeSearchTools.find_usages
                result = CodeSearchTools.find_usages(pattern, search_path=search_path)
                return result
            elif mode == "definitions":
                # Use CodeSearchTools.find_definitions
                result = CodeSearchTools.find_definitions(pattern, search_path=search_path)
                return result
            elif mode == "todos":
                # Use CodeSearchTools.find_todos
                result = CodeSearchTools.find_todos(search_path=search_path)
                return result
            elif mode == "imports":
                # Use CodeSearchTools.find_imports
                result = CodeSearchTools.find_imports(pattern, search_path=search_path)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'text', 'usages', 'definitions', 'todos', 'imports'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in code_search with mode '{mode}': {str(e)}"
            )

