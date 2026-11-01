"""
Consolidated Testing & Linting Tools
Replaces: run_tests, run_pytest, run_npm_test, run_vitest, get_test_summary, run_linter, run_formatter, fix_code, lint_python, lint_javascript, show_lint_diff
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.test_runner import TestRunnerTools
from tools.lint_tools import LintTools


class QualityTools:
    """Consolidated testing and linting tools with mode-based operations"""
    
    @staticmethod
    def test_run(test_path: str = "tests", framework: str = "auto", path: str = ".", timeout: int = None) -> ToolResult:
        """
        Uniform test execution across languages.
        
        Replaces: run_tests, run_pytest, run_npm_test, run_vitest, get_test_summary
        
        Args:
            test_path: Path to tests (default: "tests")
            framework: Test framework - "auto" (default), "pytest", "npm_test", "vitest"
            path: Project path (default: current directory)
            timeout: Timeout in seconds (optional)
        
        Returns:
            ToolResult with test results summary
        
        Examples:
            test_run(framework="auto")  # Auto-detect framework
            test_run(framework="pytest")  # Use pytest
            test_run(framework="npm_test")  # Use npm test
            test_run(framework="vitest")  # Use vitest
        """
        try:
            # Use TestRunnerTools.run_tests (handles all frameworks)
            result = TestRunnerTools.run_tests(
                test_path=test_path,
                framework=framework,
                path=path,
                timeout=timeout
            )
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in test_run: {str(e)}"
            )
    
    @staticmethod
    def lint_run(file_path: str, mode: str = "lint", language: str = "auto", auto_fix: bool = False, show_diff: bool = False) -> ToolResult:
        """
        Lint/format code in any language.
        
        Replaces: run_linter, run_formatter, fix_code, lint_python, lint_javascript, show_lint_diff
        
        Args:
            file_path: Path to file to lint/format
            mode: Operation mode:
                - "lint" (default): Run linter
                - "format": Format code
                - "fix": Auto-fix issues
            language: Programming language - "auto" (default), "python", "javascript", "typescript"
            auto_fix: Whether to auto-fix issues (for lint mode)
            show_diff: Whether to show diff (for format/fix modes)
        
        Returns:
            ToolResult with lint/format results based on mode
        
        Examples:
            lint_run("src/main.py", mode="lint")  # Lint Python code
            lint_run("src/main.py", mode="format")  # Format Python code
            lint_run("src/main.py", mode="fix", auto_fix=True)  # Auto-fix issues
            lint_run("src/app.js", mode="lint", language="javascript")  # Lint JavaScript
        """
        try:
            if mode == "lint":
                # Use LintTools.run_linter
                if language == "python":
                    result = LintTools.lint_python(file_path, fix=auto_fix)
                elif language == "javascript" or language == "typescript":
                    result = LintTools.lint_javascript(file_path, fix=auto_fix)
                else:
                    result = LintTools.run_linter(file_path, tool="auto", fix=auto_fix)
                return result
            elif mode == "format":
                # Use LintTools.run_formatter
                result = LintTools.run_formatter(file_path, language=language, show_diff=show_diff)
                return result
            elif mode == "fix":
                # Use LintTools.fix_code
                result = LintTools.fix_code(file_path, language=language, show_diff=show_diff)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'lint', 'format', 'fix'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in lint_run with mode '{mode}': {str(e)}"
            )

