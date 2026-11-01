"""
Lint and format tools for agents to ensure code quality and style consistency
"""
import subprocess
import tempfile
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, List

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from agents.timeout_config import TIMEOUT_CONFIG


class LintTools:
    """Tools for running linters and formatters"""
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _detect_language(filepath: Path) -> str:
        """Detect programming language from file extension"""
        extension = filepath.suffix.lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }
        
        return language_map.get(extension, "unknown")
    
    @staticmethod
    def _detect_linter(filepath: Path, language: str) -> str:
        """Auto-detect linter/formatter for file"""
        if language == "python":
            # Check for black
            try:
                result = subprocess.run(
                    ["python3", "-m", "black", "--version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return "black"
            except:
                pass
            
            # Check for flake8
            try:
                result = subprocess.run(
                    ["python3", "-m", "flake8", "--version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return "flake8"
            except:
                pass
            
            return "black"  # Default to black
        
        elif language in ["javascript", "typescript"]:
            # Check for eslint
            try:
                result = subprocess.run(
                    ["npx", "eslint", "--version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return "eslint"
            except:
                pass
            
            # Check for prettier
            try:
                result = subprocess.run(
                    ["npx", "prettier", "--version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return "prettier"
            except:
                pass
            
            return "prettier"  # Default to prettier
        
        return "unknown"
    
    @staticmethod
    def run_linter(
        filepath: str,
        tool: str = "auto",
        fix: bool = False,
        path: str = "."
    ) -> ToolResult:
        """
        Run linter, optionally fix issues.
        
        Args:
            filepath: File to lint
            tool: Linter tool ("auto", "black", "flake8", "eslint", "prettier")
            fix: Whether to auto-fix issues (default: False)
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with linting results
        """
        try:
            # Validate path
            is_safe, error = LintTools._is_safe_path(filepath)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "File path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            file_path = (project_path / filepath).resolve()
            
            if not file_path.exists() or not file_path.is_file():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"File not found: {filepath}"
                )
            
            # Detect language
            language = LintTools._detect_language(file_path)
            if language == "unknown":
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unknown file type: {file_path.suffix}"
                )
            
            # Auto-detect tool if needed
            if tool == "auto":
                tool = LintTools._detect_linter(file_path, language)
                if tool == "unknown":
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Could not auto-detect linter for {language}"
                    )
            
            # Run appropriate linter
            if language == "python":
                if tool == "black":
                    return LintTools.lint_python(filepath, "black", fix, project_path)
                elif tool == "flake8":
                    return LintTools.lint_python(filepath, "flake8", fix, project_path)
                else:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Unsupported Python linter: {tool}"
                    )
            
            elif language in ["javascript", "typescript"]:
                return LintTools.lint_javascript(filepath, tool, fix, project_path)
            
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Linting not supported for language: {language}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running linter: {str(e)}"
            )
    
    @staticmethod
    def run_formatter(
        filepath: str,
        tool: str = "auto",
        path: str = "."
    ) -> ToolResult:
        """
        Run formatter, return formatted code or diff.
        
        Args:
            filepath: File to format
            tool: Formatter tool ("auto", "black", "prettier")
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with formatted code or diff
        """
        try:
            # Use linter with fix=True for formatting
            result = LintTools.run_linter(filepath, tool, fix=True, path=path)
            
            if not result.success:
                return result
            
            # Return formatted result
            return ToolResult(
                success=True,
                result=result.result,
                metadata={
                    "formatted": True,
                    "tool": tool
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running formatter: {str(e)}"
            )
    
    @staticmethod
    def lint_python(
        filepath: str,
        tool: str = "black",
        fix: bool = False,
        path: Path = None
    ) -> ToolResult:
        """
        Run Python linter (black/flake8).
        
        Args:
            filepath: Python file to lint
            tool: Linter tool ("black", "flake8")
            fix: Whether to auto-fix (default: False)
            path: Project path
        
        Returns:
            ToolResult with linting results
        """
        try:
            if path is None:
                path = Path.cwd()
            
            file_path = path / filepath
            
            if tool == "black":
                # Black formatter/linter
                if fix:
                    # Format the file
                    result = subprocess.run(
                        ["python3", "-m", "black", str(file_path)],
                        cwd=str(path),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        # Read formatted file
                        formatted_content = file_path.read_text(encoding='utf-8')
                        return ToolResult(
                            success=True,
                            result={
                                "formatted": True,
                                "content": formatted_content,
                                "tool": "black"
                            },
                            metadata={
                                "tool": "black",
                                "fixed": True
                            }
                        )
                    else:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"Black formatting failed: {result.stderr}"
                        )
                else:
                    # Check formatting without fixing
                    result = subprocess.run(
                        ["python3", "-m", "black", "--check", "--diff", str(file_path)],
                        cwd=str(path),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    return ToolResult(
                        success=result.returncode == 0,
                        result={
                            "needs_formatting": result.returncode != 0,
                            "diff": result.stdout if result.returncode != 0 else "",
                            "tool": "black"
                        },
                        error=result.stderr if result.returncode != 0 else "",
                        metadata={
                            "tool": "black",
                            "needs_formatting": result.returncode != 0
                        }
                    )
            
            elif tool == "flake8":
                # Flake8 linter
                result = subprocess.run(
                    ["python3", "-m", "flake8", str(file_path)],
                    cwd=str(path),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                issues = []
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            # Parse flake8 output: file:line:col: code message
                            parts = line.split(':', 3)
                            if len(parts) >= 4:
                                issues.append({
                                    "file": parts[0],
                                    "line": parts[1],
                                    "column": parts[2],
                                    "code": parts[3].split()[0] if parts[3].split() else "",
                                    "message": parts[3]
                                })
                
                return ToolResult(
                    success=result.returncode == 0,
                    result={
                        "issues": issues,
                        "count": len(issues),
                        "tool": "flake8"
                    },
                    error=result.stderr if result.returncode != 0 else "",
                    metadata={
                        "tool": "flake8",
                        "issue_count": len(issues)
                    }
                )
            
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported Python linter: {tool}"
                )
        
        except FileNotFoundError:
            tool_name = "black" if tool == "black" else "flake8"
            return ToolResult(
                success=False,
                result=None,
                error=f"{tool_name} not found. Install with: pip install {tool_name}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=None,
                error="Linting timed out after 10s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running {tool}: {str(e)}"
            )
    
    @staticmethod
    def lint_javascript(
        filepath: str,
        tool: str = "prettier",
        fix: bool = False,
        path: Path = None
    ) -> ToolResult:
        """
        Run JavaScript/TypeScript linter (eslint/prettier).
        
        Args:
            filepath: JS/TS file to lint
            tool: Linter tool ("eslint", "prettier")
            fix: Whether to auto-fix (default: False)
            path: Project path
        
        Returns:
            ToolResult with linting results
        """
        try:
            if path is None:
                path = Path.cwd()
            
            file_path = path / filepath
            
            if tool == "prettier":
                # Prettier formatter
                if fix:
                    # Format the file
                    result = subprocess.run(
                        ["npx", "prettier", "--write", str(file_path)],
                        cwd=str(path),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        formatted_content = file_path.read_text(encoding='utf-8')
                        return ToolResult(
                            success=True,
                            result={
                                "formatted": True,
                                "content": formatted_content,
                                "tool": "prettier"
                            },
                            metadata={
                                "tool": "prettier",
                                "fixed": True
                            }
                        )
                    else:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"Prettier formatting failed: {result.stderr}"
                        )
                else:
                    # Check formatting without fixing
                    result = subprocess.run(
                        ["npx", "prettier", "--check", str(file_path)],
                        cwd=str(path),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    return ToolResult(
                        success=result.returncode == 0,
                        result={
                            "needs_formatting": result.returncode != 0,
                            "tool": "prettier"
                        },
                        error=result.stderr if result.returncode != 0 else "",
                        metadata={
                            "tool": "prettier",
                            "needs_formatting": result.returncode != 0
                        }
                    )
            
            elif tool == "eslint":
                # ESLint linter
                cmd = ["npx", "eslint", str(file_path)]
                if fix:
                    cmd.append("--fix")
                
                result = subprocess.run(
                    cmd,
                    cwd=str(path),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                issues = []
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if 'error' in line.lower() or 'warning' in line.lower():
                            issues.append(line)
                
                return ToolResult(
                    success=result.returncode == 0,
                    result={
                        "issues": issues,
                        "count": len(issues),
                        "tool": "eslint",
                        "fixed": fix
                    },
                    error=result.stderr if result.returncode != 0 else "",
                    metadata={
                        "tool": "eslint",
                        "issue_count": len(issues),
                        "fixed": fix
                    }
                )
            
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported JavaScript linter: {tool}"
                )
        
        except FileNotFoundError:
            return ToolResult(
                success=False,
                result=None,
                error=f"{tool} not found. Install with: npm install -D {tool}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=None,
                error="Linting timed out after 10s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running {tool}: {str(e)}"
            )
    
    @staticmethod
    def fix_code(
        filepath: str,
        tool: str = "auto",
        path: str = "."
    ) -> ToolResult:
        """
        Auto-fix linting issues.
        
        Args:
            filepath: File to fix
            tool: Linter tool ("auto", "black", "flake8", "eslint", "prettier")
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with fixed code
        """
        return LintTools.run_linter(filepath, tool, fix=True, path=path)
    
    @staticmethod
    def show_lint_diff(
        filepath: str,
        tool: str = "auto",
        path: str = "."
    ) -> ToolResult:
        """
        Show what would be fixed (diff).
        
        Args:
            filepath: File to check
            tool: Formatter tool ("auto", "black", "prettier")
            path: Project path (default: current directory)
        
        Returns:
            ToolResult with diff
        """
        try:
            # Validate path
            is_safe, error = LintTools._is_safe_path(filepath)
            if not is_safe:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error or "File path is not safe to access"
                )
            
            project_path = Path(path).resolve()
            file_path = (project_path / filepath).resolve()
            
            if not file_path.exists() or not file_path.is_file():
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"File not found: {filepath}"
                )
            
            # Detect language and tool
            language = LintTools._detect_language(file_path)
            if tool == "auto":
                tool = LintTools._detect_linter(file_path, language)
            
            # Get original content
            original_content = file_path.read_text(encoding='utf-8')
            
            # Run formatter without fixing
            if language == "python" and tool == "black":
                result = subprocess.run(
                    ["python3", "-m", "black", "--check", "--diff", str(file_path)],
                    cwd=str(project_path),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                diff = result.stdout if result.returncode != 0 else ""
                
                return ToolResult(
                    success=True,
                    result={
                        "diff": diff,
                        "has_changes": bool(diff),
                        "tool": "black"
                    },
                    metadata={
                        "tool": "black",
                        "has_changes": bool(diff)
                    }
                )
            
            elif language in ["javascript", "typescript"] and tool == "prettier":
                # Prettier doesn't have a --diff option, so we format to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix=file_path.suffix, delete=False) as temp_file:
                    temp_path = Path(temp_file.name)
                    temp_path.write_text(original_content, encoding='utf-8')
                
                try:
                    # Format temp file
                    result = subprocess.run(
                        ["npx", "prettier", "--write", str(temp_path)],
                        cwd=str(project_path),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        # Read formatted content
                        formatted_content = temp_path.read_text(encoding='utf-8')
                        
                        # Generate diff
                        diff_lines = list(difflib.unified_diff(
                            original_content.splitlines(keepends=True),
                            formatted_content.splitlines(keepends=True),
                            fromfile=filepath,
                            tofile=filepath + " (formatted)"
                        ))
                        diff = ''.join(diff_lines)
                        
                        return ToolResult(
                            success=True,
                            result={
                                "diff": diff,
                                "has_changes": bool(diff),
                                "tool": "prettier"
                            },
                            metadata={
                                "tool": "prettier",
                                "has_changes": bool(diff)
                            }
                        )
                    else:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"Prettier failed: {result.stderr}"
                        )
                finally:
                    temp_path.unlink(missing_ok=True)
            
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Diff not supported for tool: {tool}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error showing diff: {str(e)}"
            )

