"""
Consolidated Code Quality & Execution Tools
Replaces: check_syntax, check_types, analyze_complexity, format_code, organize_imports, apply_code_quality, execute_code
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult, CodeTools


class CodeQualityTools:
    """Consolidated code quality and execution tools with mode-based operations"""
    
    @staticmethod
    def code_check(code: str, mode: str = "syntax") -> ToolResult:
        """
        Validate syntax, types, and static complexity.
        
        Replaces: check_syntax, check_types, analyze_complexity
        
        Args:
            code: Code to check
            mode: Operation mode:
                - "syntax" (default): Check syntax validity
                - "types": Type checking
                - "complexity": Analyze code complexity
        
        Returns:
            ToolResult with validation results based on mode
        
        Examples:
            code_check("def main(): pass", mode="syntax")  # Check syntax
            code_check("def main() -> int: return 5", mode="types")  # Type check
            code_check("def complex_func(): ...", mode="complexity")  # Analyze complexity
        """
        try:
            if mode == "syntax":
                # Use CodeTools.check_syntax
                result = CodeTools.check_syntax(code)
                return result
            elif mode == "types":
                # Use CodeTools.check_types (exists in CodeTools)
                try:
                    result = CodeTools.check_types(code)
                    return result
                except AttributeError:
                    # Fallback if check_types doesn't exist
                    return ToolResult(
                        success=False,
                        result=None,
                        error="Type checking not available. Install mypy or pyright."
                    )
            elif mode == "complexity":
                # Use CodeTools.analyze_complexity
                result = CodeTools.analyze_complexity(code)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'syntax', 'types', 'complexity'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in code_check with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def code_format(code: str, mode: str = "format") -> ToolResult:
        """
        Run formatters, organize imports, apply quality fixes.
        
        Replaces: format_code, organize_imports, apply_code_quality
        
        Args:
            code: Code to format
            mode: Operation mode:
                - "format" (default): Format code
                - "imports": Organize imports
                - "quality": Apply code quality improvements
        
        Returns:
            ToolResult with formatted code based on mode
        
        Examples:
            code_format("def main():  pass", mode="format")  # Format code
            code_format("import os\\nimport sys", mode="imports")  # Organize imports
            code_format("def main(): ...", mode="quality")  # Apply quality fixes
        """
        try:
            if mode == "format":
                # Use CodeTools.format_code
                result = CodeTools.format_code(code)
                return result
            elif mode == "imports":
                # Use CodeTools.organize_imports
                result = CodeTools.organize_imports(code)
                return result
            elif mode == "quality":
                # Use CodeTools.apply_code_quality
                result = CodeTools.apply_code_quality(code)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'format', 'imports', 'quality'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in code_format with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def code_execute(code: str, timeout: int = None) -> ToolResult:
        """
        Run code safely inside a sandbox.
        
        Replaces: execute_code
        
        Args:
            code: Code to execute
            timeout: Timeout in seconds (optional)
        
        Returns:
            ToolResult with execution output
        
        Examples:
            code_execute("print('Hello')")  # Execute code
            code_execute("x = 5; print(x)", timeout=5)  # With timeout
        """
        try:
            # Use CodeTools.execute_code
            result = CodeTools.execute_code(code, timeout=timeout)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in code_execute: {str(e)}"
            )

