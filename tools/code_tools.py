"""
Tools that agents can use to verify their work
"""

import subprocess
import ast
import os
import tempfile
import re
from typing import Dict, Any
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.timeout_config import TIMEOUT_CONFIG

# File tools will be imported lazily after TOOL_REGISTRY is created
FILE_TOOLS_AVAILABLE = False
FileTools = None

@dataclass
class ToolResult:
    """Standardized tool output"""
    success: bool
    result: Any
    error: str = ""
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata or {}
        }
    
    def to_prompt(self):
        """Format for agent consumption"""
        if self.success:
            return f"✓ Success: {self.result}"
        else:
            return f"✗ Error: {self.error}"


class CodeTools:
    """Tools for code validation and execution"""
    
    @staticmethod
    def check_syntax(code: str) -> ToolResult:
        """
        Check if Python code is syntactically valid
        
        Usage from agent:
        TOOL: check_syntax
        INPUT: <your code>
        """
        try:
            # Extract code from markdown if needed
            clean_code = CodeTools._extract_code(code)
            
            # Try to parse
            ast.parse(clean_code)
            
            return ToolResult(
                success=True,
                result="Code is syntactically valid",
                metadata={"lines": len(clean_code.split('\n'))}
            )
        except SyntaxError as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Syntax error on line {e.lineno}: {e.msg}",
                metadata={"line": e.lineno}
            )
    
    @staticmethod
    def execute_code(code: str, timeout: int = None) -> ToolResult:
        """
        Execute Python code and return output
        
        SECURITY: Runs in subprocess with timeout
        
        Args:
            code: Python code to execute
            timeout: Timeout in seconds (default: from config)
        """
        # Get timeout from config if not provided
        if timeout is None:
            timeout = TIMEOUT_CONFIG.get_code_execution_timeout()
        
        try:
            clean_code = CodeTools._extract_code(code)

            # Skip execution if code requires input
            if "input(" in clean_code:
                return ToolResult(
                    success=True,
                    result="Code contains input() - skipped execution (syntax valid)",
                    metadata={"skipped": True, "reason": "interactive"},
                )

            # Skip if it's in if __name__ == "__main__" block only
            if "if __name__" in clean_code and "def " in clean_code:
                # Extract just the function, not the example usage
                lines = clean_code.split("\n")
                code_only = []
                in_main = False
                for line in lines:
                    if "if __name__" in line:
                        in_main = True
                    if not in_main:
                        code_only.append(line)
                clean_code = "\n".join(code_only)
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(clean_code)
                temp_file = f.name
            
            try:
                # Execute with timeout
                result = subprocess.run(
                    ['python3', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        result=result.stdout,
                        metadata={
                            "returncode": 0,
                            "execution_time": "< {}s".format(timeout)
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        result=result.stdout,
                        error=result.stderr,
                        metadata={"returncode": result.returncode}
                    )
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=None,
                error=f"Execution timed out after {timeout}s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    @staticmethod
    def _clean_test_file(original_code: str, test_code: str) -> str:
        """Clean and combine code for testing - remove duplicates and execution code"""
        # Extract function/class names from original code
        original_names = set()
        try:
            tree = ast.parse(original_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    original_names.add(node.name)
        except:
            pass
        
        # Simple heuristic: extract only imports and test functions from test_code
        lines = test_code.split('\n')
        cleaned_lines = []
        skip_block = False
        skip_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Always keep imports
            if stripped.startswith('import ') or stripped.startswith('from '):
                cleaned_lines.append(line)
                skip_block = False
            # Keep comments
            elif stripped.startswith('#'):
                cleaned_lines.append(line)
            # Keep test functions
            elif stripped.startswith('def test_'):
                cleaned_lines.append(line)
                skip_block = False
            # For other def/class: check if it's a duplicate
            elif stripped.startswith('def ') or stripped.startswith('class '):
                name_part = stripped.split('(')[0].split(':')[0]
                name = name_part.replace('def ', '').replace('class ', '').strip()
                if name in original_names and not name.startswith('test_'):
                    # Skip duplicate definition
                    skip_block = True
                    skip_indent = indent
                else:
                    cleaned_lines.append(line)
                    skip_block = False
            # Skip lines inside a block we're skipping (duplicate function body)
            elif skip_block and indent > skip_indent:
                continue  # Skip this line
            # Stop skipping when we reach a new top-level item
            elif skip_block and indent <= skip_indent and stripped:
                skip_block = False
                # Re-process this line
                if stripped.startswith('def test_'):
                    cleaned_lines.append(line)
            # Skip execution code at module level (not in a function/class)
            elif not skip_block and indent == 0 and stripped:
                if stripped.startswith('print(') or (stripped.count('=') > 0 and '==' not in stripped and 'assert' not in stripped):
                    continue  # Skip execution statements
                else:
                    cleaned_lines.append(line)
            # Keep everything else (inside functions/classes we're keeping)
            else:
                if not skip_block:
                    cleaned_lines.append(line)
        
        cleaned_test = '\n'.join(cleaned_lines)
        return f"{original_code}\n\n# Tests\n{cleaned_test}"
    
    @staticmethod
    def run_tests(code: str, test_code: str = None, timeout: int = None) -> ToolResult:
        """
        Run pytest on code
        If test_code provided, combines them intelligently
        """
        try:
            clean_code = CodeTools._extract_code(code)
            
            # If test code provided separately, clean and combine
            if test_code:
                clean_test = CodeTools._extract_code(test_code)
                full_code = CodeTools._clean_test_file(clean_code, clean_test)
            else:
                full_code = clean_code
            
            # Validate syntax before running tests
            try:
                ast.parse(full_code)
            except SyntaxError as e:
                return ToolResult(
                    success=False,
                    result="0 passed, 0 failed",
                    error=f"Syntax error in combined code: {str(e)}\nLine {e.lineno}: {e.text}",
                    metadata={
                        "passed": 0,
                        "failed": 0,
                        "total": 0,
                        "syntax_error": True
                    }
                )
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
                f.write(full_code)
                temp_file = f.name
            
            # Initialize pass/fail counts early for finally block
            passed = 0
            failed = 0
            error_count = 0
            
            try:
                # Check if pytest is available
                try:
                    pytest_check = subprocess.run(
                        ['python3', '-m', 'pytest', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    # Check both return code and stderr for missing module
                    if pytest_check.returncode != 0 or 'No module named pytest' in pytest_check.stderr:
                        # Don't delete temp_file here - finally block will handle it
                        # But mark it so finally doesn't try to debug-copy it
                        passed = -1  # Special marker to skip debug copy
                        return ToolResult(
                            success=False,
                            result="0 passed, 0 failed",
                            error=f"pytest is not installed. Install with: pip install pytest\nOutput: {pytest_check.stderr}",
                            metadata={
                                "passed": 0,
                                "failed": 0,
                                "total": 0,
                                "pytest_missing": True,
                                "install_hint": "pip install pytest"
                            }
                        )
                except Exception as e:
                    # Don't delete temp_file here - finally block will handle it
                    # But mark it so finally doesn't try to debug-copy it
                    passed = -1  # Special marker to skip debug copy
                    # If we can't even check, pytest is likely not available
                    return ToolResult(
                        success=False,
                        result="0 passed, 0 failed",
                        error=f"Cannot check pytest installation: {str(e)}\nTry installing with: pip install pytest",
                        metadata={
                            "passed": 0,
                            "failed": 0,
                            "total": 0,
                            "pytest_missing": True,
                            "install_hint": "pip install pytest"
                        }
                    )
                
                # Run pytest with more verbose error output (timeout already set above)
                result = subprocess.run(
                    ['python3', '-m', 'pytest', temp_file, '-v', '--tb=long', '--no-header'],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                # Parse output for pass/fail counts
                output = result.stdout + result.stderr
                passed = output.count(' PASSED')
                failed = output.count(' FAILED')
                error_count = output.count(' ERROR')
                
                # Check for collection errors or no tests found
                if passed == 0 and failed == 0:
                    # Look for error messages
                    if 'ERROR' in output or 'error' in output.lower():
                        error_lines = [line for line in output.split('\n') if 'error' in line.lower() or 'Error' in line]
                        error_msg = '\n'.join(error_lines[:5])  # First 5 error lines
                        if error_msg:
                            return ToolResult(
                                success=False,
                                result="0 passed, 0 failed",
                                error=f"Test collection/execution error:\n{error_msg}\n\nFull output:\n{output[-500:]}",
                                metadata={
                                    "passed": 0,
                                    "failed": 0,
                                    "total": 0,
                                    "collection_error": True,
                                    "full_output": output[-1000:]  # Last 1000 chars
                                }
                            )
                    
                    # Check if pytest found any test files
                    if 'no tests ran' in output.lower() or 'collected 0 items' in output.lower():
                        return ToolResult(
                            success=False,
                            result="0 passed, 0 failed",
                            error=f"No tests found or collected. Output:\n{output[-500:]}",
                            metadata={
                                "passed": 0,
                                "failed": 0,
                                "total": 0,
                                "no_tests": True,
                                "full_output": output[-1000:]
                            }
                        )
                
                return ToolResult(
                    success=result.returncode == 0 and failed == 0,
                    result=f"{passed} passed, {failed} failed",
                    error=output if result.returncode != 0 else "",
                    metadata={
                        "passed": passed,
                        "failed": failed,
                        "errors": error_count,
                        "total": passed + failed + error_count,
                        "full_output": output[-1000:] if passed == 0 and failed == 0 else None
                    }
                )
            finally:
                # Keep file for debugging if tests failed (but not if pytest was missing)
                if passed == 0 and failed == 0 and passed != -1:
                    debug_file = temp_file.replace('_test.py', '_debug.py')
                    try:
                        import shutil
                        shutil.copy(temp_file, debug_file)
                        print(f"      🔍 Debug: Saved test file to {debug_file}")
                    except:
                        pass
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result="0 passed, 0 failed",
                error="Tests timed out after 10s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result="0 passed, 0 failed",
                error=f"Error running tests: {str(e)}"
            )
    
    @staticmethod
    def save_file(filepath: str, content: str) -> ToolResult:
        """
        Save code to a file
        
        Creates parent directories if needed
        """
        try:
            # Ensure we're in a safe directory
            if filepath.startswith('/'):
                return ToolResult(
                    success=False,
                    result=None,
                    error="Absolute paths not allowed for security"
                )
            
            # Create in output directory
            output_dir = os.path.expanduser("~/ai-coding-team/output")
            os.makedirs(output_dir, exist_ok=True)
            
            full_path = os.path.join(output_dir, filepath)
            
            # Create parent directories
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            with open(full_path, 'w') as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                result=f"Saved to {full_path}",
                metadata={"path": full_path}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    @staticmethod
    def analyze_complexity(code: str) -> ToolResult:
        """
        Analyze code complexity metrics
        """
        try:
            clean_code = CodeTools._extract_code(code)
            
            # Basic metrics
            lines = clean_code.split('\n')
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            
            # Count functions and classes
            tree = ast.parse(clean_code)
            functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
            classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            
            metrics = {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "functions": functions,
                "classes": classes
            }
            
            return ToolResult(
                success=True,
                result=f"{code_lines} lines of code, {functions} functions, {classes} classes",
                metadata=metrics
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    @staticmethod
    def format_code(code: str) -> ToolResult:
        """
        Format Python code using black.
        
        Args:
            code: Python code to format
        
        Returns:
            ToolResult with formatted code or error message
        """
        try:
            clean_code = CodeTools._extract_code(code)
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(clean_code)
                temp_file = f.name
            
            try:
                # Try to format with black
                result = subprocess.run(
                    ['python3', '-m', 'black', '--line-length', '100', '--quiet', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    # Read formatted code
                    with open(temp_file, 'r') as f:
                        formatted_code = f.read()
                    
                    return ToolResult(
                        success=True,
                        result=formatted_code,
                        metadata={"formatted": True}
                    )
                else:
                    # Black might not be installed, check error
                    if 'No module named black' in result.stderr:
                        return ToolResult(
                            success=False,
                            result=clean_code,  # Return original code
                            error="black is not installed. Install with: pip install black",
                            metadata={"black_missing": True, "install_hint": "pip install black"}
                        )
                    else:
                        # Black failed but code might be valid - return original
                        return ToolResult(
                            success=False,
                            result=clean_code,
                            error=f"black formatting failed: {result.stderr[:200]}",
                            metadata={"black_error": result.stderr[:200]}
                        )
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=code,
                error="Formatting timed out after 5s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=code,
                error=f"Error formatting code: {str(e)}"
            )
    
    @staticmethod
    def organize_imports(code: str) -> ToolResult:
        """
        Organize imports using isort.
        
        Args:
            code: Python code with imports
        
        Returns:
            ToolResult with organized imports or error message
        """
        try:
            clean_code = CodeTools._extract_code(code)
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(clean_code)
                temp_file = f.name
            
            try:
                # Try to organize imports with isort
                result = subprocess.run(
                    ['python3', '-m', 'isort', '--line-length', '100', '--quiet', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    # Read organized code
                    with open(temp_file, 'r') as f:
                        organized_code = f.read()
                    
                    return ToolResult(
                        success=True,
                        result=organized_code,
                        metadata={"imports_organized": True}
                    )
                else:
                    # isort might not be installed
                    if 'No module named isort' in result.stderr:
                        return ToolResult(
                            success=False,
                            result=clean_code,  # Return original code
                            error="isort is not installed. Install with: pip install isort",
                            metadata={"isort_missing": True, "install_hint": "pip install isort"}
                        )
                    else:
                        # isort failed - return original
                        return ToolResult(
                            success=False,
                            result=clean_code,
                            error=f"isort organization failed: {result.stderr[:200]}",
                            metadata={"isort_error": result.stderr[:200]}
                        )
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=code,
                error="Import organization timed out after 5s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=code,
                error=f"Error organizing imports: {str(e)}"
            )
    
    @staticmethod
    def check_types(code: str) -> ToolResult:
        """
        Check type hints using mypy.
        
        Args:
            code: Python code to type check
        
        Returns:
            ToolResult with type check results
        """
        try:
            clean_code = CodeTools._extract_code(code)
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(clean_code)
                temp_file = f.name
            
            try:
                # Try to type check with mypy
                result = subprocess.run(
                    ['python3', '-m', 'mypy', '--ignore-missing-imports', '--no-error-summary', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Check if mypy is installed
                if 'No module named mypy' in result.stderr:
                    return ToolResult(
                        success=False,
                        result=code,
                        error="mypy is not installed. Install with: pip install mypy",
                        metadata={"mypy_missing": True, "install_hint": "pip install mypy"}
                    )
                
                # mypy returns 0 if no errors, 1 if errors, 2 if crash
                if result.returncode == 0:
                    return ToolResult(
                        success=True,
                        result="No type errors found",
                        metadata={"type_errors": 0}
                    )
                elif result.returncode == 1:
                    # Type errors found - parse them
                    errors = result.stdout.split('\n')
                    error_lines = [e for e in errors if 'error:' in e or 'Error' in e]
                    
                    return ToolResult(
                        success=False,
                        result=code,  # Return original code
                        error=f"Type errors found:\n" + "\n".join(error_lines[:5]),
                        metadata={
                            "type_errors": len(error_lines),
                            "errors": error_lines[:10],
                            "full_output": result.stdout
                        }
                    )
                else:
                    # mypy crashed
                    return ToolResult(
                        success=False,
                        result=code,
                        error=f"mypy crashed: {result.stderr[:200]}",
                        metadata={"mypy_crash": True}
                    )
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=code,
                error="Type checking timed out after 10s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=code,
                error=f"Error checking types: {str(e)}"
            )
    
    @staticmethod
    def apply_code_quality(code: str) -> ToolResult:
        """
        Apply all code quality tools: format, organize imports, then check types.
        
        Args:
            code: Python code to improve
        
        Returns:
            ToolResult with improved code and quality report
        """
        original_code = code
        improvements = []
        
        # Step 1: Organize imports (should be first)
        import_result = CodeTools.organize_imports(original_code)
        if import_result.success:
            code = import_result.result
            improvements.append("Imports organized")
        elif import_result.metadata and import_result.metadata.get('isort_missing'):
            improvements.append("⚠️  isort not installed (imports not organized)")
        
        # Step 2: Format code
        format_result = CodeTools.format_code(code)
        if format_result.success:
            code = format_result.result
            improvements.append("Code formatted")
        elif format_result.metadata and format_result.metadata.get('black_missing'):
            improvements.append("⚠️  black not installed (code not formatted)")
        
        # Step 3: Check types (doesn't modify code)
        type_result = CodeTools.check_types(code)
        type_info = ""
        if type_result.success:
            type_info = "No type errors"
        elif type_result.metadata and type_result.metadata.get('mypy_missing'):
            type_info = "⚠️  mypy not installed (types not checked)"
        else:
            type_info = f"Type errors: {type_result.error[:100]}"
        
        return ToolResult(
            success=True,  # Consider it success even if tools missing
            result=code,  # Return improved code
            error=type_info,  # Type check info in error field
            metadata={
                "improvements": improvements,
                "type_check": type_result.to_dict() if hasattr(type_result, 'to_dict') else {},
                "final_code": code
            }
        )
    
    @staticmethod
    def _extract_code(text: str) -> str:
        """Extract code from markdown code blocks - handles multiple blocks, removes tool call syntax"""
        # Pattern to match code blocks: ```python ... ``` or ``` ... ```
        code_blocks = []
        
        # Try to extract python blocks first
        python_pattern = r'```python\s*\n(.*?)```'
        matches = re.findall(python_pattern, text, re.DOTALL)
        if matches:
            # Combine all python code blocks
            code_blocks.extend(matches)
        
        # If no python blocks, try generic code blocks
        if not code_blocks:
            generic_pattern = r'```[a-z]*\s*\n(.*?)```'
            matches = re.findall(generic_pattern, text, re.DOTALL)
            if matches:
                code_blocks.extend(matches)
        
        # If we found code blocks, join them with newlines
        if code_blocks:
            extracted = '\n\n'.join(block.strip() for block in code_blocks)
        else:
            # No code blocks found, return text as-is (might already be pure code)
            extracted = text.strip()
        
        # Remove tool call syntax that might be in the code
        lines = extracted.split('\n')
        cleaned_lines = []
        skip_tool_section = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip tool call markers
            if stripped.startswith('TOOL:') or stripped.startswith('TOOL RESULTS:') or stripped.startswith('INPUT:'):
                skip_tool_section = True
                continue
            
            # Skip lines that look like tool results
            if skip_tool_section:
                # Stop skipping when we hit a line that doesn't look like tool output
                if not (stripped.startswith('- ') or stripped.startswith('{') or stripped.startswith('}') or 
                        (':' in stripped and not stripped.startswith('def ') and not stripped.startswith('class ') and 
                         not stripped.startswith('import ') and not stripped.startswith('from '))):
                    skip_tool_section = False
                else:
                    continue
            
            # Skip tool result lines
            if stripped.startswith('- ') and ('tool' in stripped.lower() or 'result' in stripped.lower()):
                continue
            
            cleaned_lines.append(line)
        
        cleaned = '\n'.join(cleaned_lines)
        
        # Remove any stray markdown artifacts
        cleaned = re.sub(r'^#+\s*', '', cleaned, flags=re.MULTILINE)
        
        return cleaned.strip()


# Tool registry - maps names to functions
TOOL_REGISTRY = {
    "check_syntax": {
        "function": CodeTools.check_syntax,
        "description": "Check if Python code is syntactically valid"
    },
    "execute_code": {
        "function": CodeTools.execute_code,
        "description": "Execute Python code and return output (5s timeout)"
    },
    "run_tests": {
        "function": CodeTools.run_tests,
        "description": "Run pytest on code with tests"
    },
    "save_file": {
        "function": CodeTools.save_file,
        "description": "Save code to a file in output directory"
    },
    "analyze_complexity": {
        "function": CodeTools.analyze_complexity,
        "description": "Analyze code metrics (lines, functions, classes)"
    },
    "format_code": {
        "function": CodeTools.format_code,
        "description": "Format Python code using black"
    },
    "organize_imports": {
        "function": CodeTools.organize_imports,
        "description": "Organize imports using isort"
    },
    "check_types": {
        "function": CodeTools.check_types,
        "description": "Check type hints using mypy"
    },
    "apply_code_quality": {
        "function": CodeTools.apply_code_quality,
        "description": "Apply all code quality tools: format, organize imports, check types"
    }
}

# Add file tools if available (lazy import)
def _register_file_tools():
    """Register file tools in TOOL_REGISTRY"""
    global FILE_TOOLS_AVAILABLE, FileTools
    try:
        from tools.file_tools import FileTools as FT
        FileTools = FT
        FILE_TOOLS_AVAILABLE = True
        
        TOOL_REGISTRY.update({
            "read_file": {
                "function": FileTools.read_file,
                "description": "Read file contents (security: only files in project directory)"
            },
            "write_file": {
                "function": FileTools.write_file,
                "description": "Write file, creating directories if needed (security: only in project directory)"
            },
            "list_directory": {
                "function": FileTools.list_directory,
                "description": "List files and directories in a directory"
            },
            "file_exists": {
                "function": FileTools.file_exists,
                "description": "Check if file exists"
            },
            "create_directory": {
                "function": FileTools.create_directory,
                "description": "Create directory structure"
            },
            "find_files": {
                "function": FileTools.find_files,
                "description": "Find files matching pattern (glob)"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        FILE_TOOLS_AVAILABLE = False
        FileTools = None
        return False

# Register file tools immediately
_register_file_tools()

# Add database tools if available (lazy import)
def _register_database_tools():
    """Register database tools in TOOL_REGISTRY"""
    try:
        from tools.database_tools import DatabaseTools as DT
        TOOL_REGISTRY.update({
            "db_connect": {
                "function": DT.connect,
                "description": "Test database connection (read-only)"
            },
            "db_query": {
                "function": DT.query,
                "description": "Execute SQL query (read-only by default: SELECT/SHOW/DESCRIBE only)"
            },
            "db_get_schema": {
                "function": DT.get_schema,
                "description": "Get table schema (columns, types, constraints)"
            },
            "db_list_tables": {
                "function": DT.list_tables,
                "description": "List all tables in database"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register database tools immediately
_register_database_tools()

# Add API testing tools if available (lazy import)
def _register_api_tools():
    """Register API testing tools in TOOL_REGISTRY"""
    try:
        from tools.api_tools import APITools as AT
        TOOL_REGISTRY.update({
            "api_start_server": {
                "function": AT.start_test_server,
                "description": "Start test server in background (localhost only, for security)"
            },
            "api_stop_server": {
                "function": AT.stop_test_server,
                "description": "Stop test server"
            },
            "api_test_endpoint": {
                "function": AT.test_endpoint,
                "description": "Test API endpoint and return response (localhost only, for security)"
            },
            "api_validate_response": {
                "function": AT.validate_response,
                "description": "Validate API response matches expected schema"
            },
            "api_test_auth": {
                "function": AT.test_authentication,
                "description": "Test authentication on protected endpoint (localhost only)"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register API testing tools immediately
_register_api_tools()

# Add web scraper tools if available (lazy import)
def _register_web_scraper_tools():
    """Register web scraper tools in TOOL_REGISTRY"""
    try:
        from tools.web_scraper import WebScraperTools as WST
        TOOL_REGISTRY.update({
            "scrape_website": {
                "function": WST.scrape_website,
                "description": "Scrape website HTML, CSS, and structure (respects robots.txt, rate-limited, security: only public URLs)"
            },
            "extract_design_elements": {
                "function": WST.extract_design_elements,
                "description": "Extract design elements from HTML/CSS: colors, fonts, layout patterns, components, spacing"
            },
            "extract_structure": {
                "function": WST.extract_structure,
                "description": "Extract website structure: navigation, layout, component hierarchy"
            },
            "analyze_design": {
                "function": WST.analyze_design,
                "description": "Analyze website design and create summary: style, color scheme, typography, layout, component patterns"
            },
            "download_assets": {
                "function": WST.download_assets,
                "description": "Get asset URLs (images, fonts, CSS files) from website (returns URLs only for security)"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register web scraper tools immediately
_register_web_scraper_tools()

# Add project scanner tools if available (lazy import)
def _register_project_scanner_tools():
    """Register project scanner tools in TOOL_REGISTRY"""
    try:
        from tools.project_scanner import ProjectScanner as PS
        TOOL_REGISTRY.update({
            "scan_project": {
                "function": PS.scan_project,
                "description": "Scan project directory and return structured summary: source dirs, entry points, configs, tests, frameworks"
            },
            "find_entrypoints": {
                "function": PS.find_entrypoints,
                "description": "Find application entry points (main.py, app.py, index.js, etc.)"
            },
            "list_configs": {
                "function": PS.list_configs,
                "description": "List configuration files (requirements.txt, package.json, config.yaml, etc.)"
            },
            "find_tests": {
                "function": PS.find_tests,
                "description": "Find test files and test directories"
            },
            "find_env_files": {
                "function": PS.find_env_files,
                "description": "Find environment files (.env, .env.example, etc.)"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register project scanner tools immediately
_register_project_scanner_tools()

# Add code search tools if available (lazy import)
def _register_code_search_tools():
    """Register code search tools in TOOL_REGISTRY"""
    try:
        from tools.code_search import CodeSearchTools as CST
        TOOL_REGISTRY.update({
            "search_code": {
                "function": CST.search_code,
                "description": "Search for string/regex across codebase. Returns file:line:snippet for each match"
            },
            "find_usages": {
                "function": CST.find_usages,
                "description": "Find where function/variable is used in codebase"
            },
            "find_definitions": {
                "function": CST.find_definitions,
                "description": "Find where function/class is defined in codebase"
            },
            "find_todos": {
                "function": CST.find_todos,
                "description": "Find TODO/FIXME comments in codebase"
            },
            "find_imports": {
                "function": CST.find_imports,
                "description": "Find imports of a module in codebase"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register code search tools immediately
_register_code_search_tools()

# Add git tools if available (lazy import)
def _register_git_tools():
    """Register git tools in TOOL_REGISTRY"""
    try:
        from tools.git_tools import GitTools as GT
        TOOL_REGISTRY.update({
            "git_status": {
                "function": GT.git_status,
                "description": "Get git status (read-only, security: only in project directory)"
            },
            "git_diff": {
                "function": GT.git_diff,
                "description": "Show git diff for files (read-only, security: only in project directory)"
            },
            "git_log": {
                "function": GT.git_log,
                "description": "Show git commit history (read-only, security: only in project directory)"
            },
            "git_show": {
                "function": GT.git_show,
                "description": "Show file at specific commit (read-only, security: only in project directory)"
            },
            "git_branch": {
                "function": GT.git_branch,
                "description": "List git branches (read-only, security: only in project directory)"
            },
            "git_add": {
                "function": GT.git_add,
                "description": "Stage files (guarded write, security: only in project directory)"
            },
            "git_commit": {
                "function": GT.git_commit,
                "description": "Commit changes (guarded write, security: only in project directory)"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register git tools immediately
_register_git_tools()

# Add task runner tools if available (lazy import)
def _register_task_runner_tools():
    """Register task runner tools in TOOL_REGISTRY"""
    try:
        from tools.task_runner import TaskRunnerTools as TRT
        TOOL_REGISTRY.update({
            "run_task": {
                "function": TRT.run_task,
                "description": "Run whitelisted task/command safely (security: only allowed commands)"
            },
            "list_tasks": {
                "function": TRT.list_tasks,
                "description": "List available tasks from package.json, Makefile, etc."
            },
            "validate_task": {
                "function": TRT.validate_task,
                "description": "Validate if task string is allowed (security check)"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register task runner tools immediately
_register_task_runner_tools()

# Add test runner tools if available (lazy import)
def _register_test_runner_tools():
    """Register test runner tools in TOOL_REGISTRY"""
    try:
        from tools.test_runner import TestRunnerTools as TRT
        TOOL_REGISTRY.update({
            "run_tests": {
                "function": TRT.run_tests,
                "description": "Run tests (auto-detect framework: pytest, npm test, vitest). Returns passed/failed counts and failing test names"
            },
            "run_pytest": {
                "function": TRT.run_pytest,
                "description": "Run pytest tests specifically"
            },
            "run_npm_test": {
                "function": TRT.run_npm_test,
                "description": "Run npm test"
            },
            "run_vitest": {
                "function": TRT.run_vitest,
                "description": "Run vitest tests"
            },
            "get_test_summary": {
                "function": TRT.get_test_summary,
                "description": "Parse test results and return structured summary"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register test runner tools immediately
_register_test_runner_tools()

# Add lint tools if available (lazy import)
def _register_lint_tools():
    """Register lint tools in TOOL_REGISTRY"""
    try:
        from tools.lint_tools import LintTools as LT
        TOOL_REGISTRY.update({
            "run_linter": {
                "function": LT.run_linter,
                "description": "Run linter (auto-detect: black, flake8, eslint, prettier). Optionally fix issues"
            },
            "run_formatter": {
                "function": LT.run_formatter,
                "description": "Run formatter (auto-detect: black, prettier). Returns formatted code"
            },
            "fix_code": {
                "function": LT.fix_code,
                "description": "Auto-fix linting issues in file"
            },
            "lint_python": {
                "function": LT.lint_python,
                "description": "Run Python linter (black/flake8). Optionally fix issues"
            },
            "lint_javascript": {
                "function": LT.lint_javascript,
                "description": "Run JavaScript/TypeScript linter (eslint/prettier). Optionally fix issues"
            },
            "show_lint_diff": {
                "function": LT.show_lint_diff,
                "description": "Show what would be fixed (diff) without applying changes"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register lint tools immediately
_register_lint_tools()

# Add docker tools if available (lazy import)
def _register_docker_tools():
    """Register docker tools in TOOL_REGISTRY"""
    try:
        from tools.docker_tools import DockerTools as DT
        TOOL_REGISTRY.update({
            "docker_ps": {
                "function": DT.docker_ps,
                "description": "List running Docker containers (read-only, security: safe operations only)"
            },
            "docker_compose_ps": {
                "function": DT.docker_compose_ps,
                "description": "List docker-compose services (read-only, security: safe operations only)"
            },
            "docker_logs": {
                "function": DT.docker_logs,
                "description": "Get container logs (read-only, security: safe operations only)"
            },
            "docker_health": {
                "function": DT.docker_health,
                "description": "Check container health (read-only, security: safe operations only)"
            },
            "docker_status": {
                "function": DT.docker_status,
                "description": "Get overall Docker status (read-only, security: safe operations only)"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register docker tools immediately
_register_docker_tools()

# Add log reader tools if available (lazy import)
def _register_log_reader_tools():
    """Register log reader tools in TOOL_REGISTRY"""
    try:
        from tools.log_reader import LogReaderTools as LRT
        TOOL_REGISTRY.update({
            "read_log": {
                "function": LRT.read_log,
                "description": "Read log file with optional filtering (keyword, level, time range). Security: only files in project directory"
            },
            "tail_log": {
                "function": LRT.tail_log,
                "description": "Get last N lines of log file. Security: only files in project directory"
            },
            "search_log": {
                "function": LRT.search_log,
                "description": "Search logs by keyword. Security: only files in project directory"
            },
            "filter_log": {
                "function": LRT.filter_log,
                "description": "Filter logs by level, keyword, or time range. Security: only files in project directory"
            },
            "list_logs": {
                "function": LRT.list_logs,
                "description": "List available log files in project"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register log reader tools immediately
_register_log_reader_tools()

# Add documentation tools if available (lazy import)
def _register_documentation_tools():
    """Register documentation tools in TOOL_REGISTRY"""
    try:
        from tools.documentation_tools import DocumentationTools as DCT
        TOOL_REGISTRY.update({
            "generate_readme": {
                "function": DCT.generate_readme,
                "description": "Generate README.md from project structure. Security: only files in project directory"
            },
            "generate_api_docs": {
                "function": DCT.generate_api_docs,
                "description": "Generate API documentation (OpenAPI/Swagger) from code. Detects Flask, FastAPI, Django routes"
            },
            "generate_code_comments": {
                "function": DCT.generate_code_comments,
                "description": "Add/improve code comments in Python files. Security: only files in project directory"
            },
            "extract_api_spec": {
                "function": DCT.extract_api_spec,
                "description": "Extract API specification from code (returns OpenAPI spec)"
            },
            "update_changelog": {
                "function": DCT.update_changelog,
                "description": "Update CHANGELOG.md with new version and changes. Security: only files in project directory"
            },
            "generate_architecture_doc": {
                "function": DCT.generate_architecture_doc,
                "description": "Generate architecture documentation from project structure"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register documentation tools immediately
_register_documentation_tools()

# Add package manager tools if available (lazy import)
def _register_package_manager_tools():
    """Register package manager tools in TOOL_REGISTRY"""
    try:
        from tools.package_manager import PackageManagerTools as PMT
        TOOL_REGISTRY.update({
            "check_dependencies": {
                "function": PMT.check_dependencies,
                "description": "Check for outdated packages. Supports Python (requirements.txt) and Node.js (package.json)"
            },
            "check_security": {
                "function": PMT.check_security,
                "description": "Check for known vulnerabilities using pip check and npm audit. Returns security issues"
            },
            "update_dependencies": {
                "function": PMT.update_dependencies,
                "description": "Update packages with optional testing after update. Security: only updates packages in project files"
            },
            "list_dependencies": {
                "function": PMT.list_dependencies,
                "description": "List all dependencies from requirements.txt and package.json"
            },
            "add_dependency": {
                "function": PMT.add_dependency,
                "description": "Add new dependency to requirements.txt or package.json. Security: only modifies project files"
            },
            "remove_dependency": {
                "function": PMT.remove_dependency,
                "description": "Remove dependency from requirements.txt or package.json. Security: only modifies project files"
            },
            "check_license": {
                "function": PMT.check_license,
                "description": "Check dependency licenses. Supports Python and Node.js packages"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register package manager tools immediately
_register_package_manager_tools()

# Add security scanning tools if available (lazy import)
def _register_security_tools():
    """Register security scanning tools in TOOL_REGISTRY"""
    try:
        from tools.security_tools import SecurityTools as ST
        TOOL_REGISTRY.update({
            "scan_security": {
                "function": ST.scan_security,
                "description": "Scan for security vulnerabilities (secrets, SQL injection, XSS, dependencies). Returns all found issues"
            },
            "check_secrets": {
                "function": ST.check_secrets,
                "description": "Check for exposed secrets/API keys in code. Security: scans project files only"
            },
            "analyze_dependencies": {
                "function": ST.analyze_dependencies,
                "description": "Analyze dependency security vulnerabilities. Uses npm audit and pip check"
            },
            "check_sql_injection": {
                "function": ST.check_sql_injection,
                "description": "Check for SQL injection risks in code. Scans for unsafe query patterns"
            },
            "check_xss": {
                "function": ST.check_xss,
                "description": "Check for XSS vulnerabilities in JavaScript/HTML files. Scans for unsafe DOM manipulation"
            },
            "security_audit": {
                "function": ST.security_audit,
                "description": "Full security audit - scans all security aspects and provides recommendations"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register security scanning tools immediately
_register_security_tools()

# Add web research tools if available (lazy import)
def _register_web_research_tools():
    """Register web research tools in TOOL_REGISTRY"""
    try:
        from tools.web_research import WebResearchTools as WRT
        TOOL_REGISTRY.update({
            "read_web_page": {
                "function": WRT.read_web_page,
                "description": "Read and extract information from web page. Returns content, summary, code examples. Security: public URLs only, rate-limited"
            },
            "read_documentation": {
                "function": WRT.read_documentation,
                "description": "Read documentation sites for specific topics. Optimized for docs.python.org, pypi.org, etc. Security: public URLs only"
            },
            "extract_information": {
                "function": WRT.extract_information,
                "description": "Extract specific information from web page (code examples, API reference, version, installation). Security: public URLs only"
            },
            "get_web_summary": {
                "function": WRT.get_web_summary,
                "description": "Get summary of web page content (useful for quick reference). Security: public URLs only"
            },
            "search_web": {
                "function": WRT.search_web,
                "description": "Search the web using DuckDuckGo (no API key needed). Returns search results with URLs. Security: rate-limited, public search only"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register web research tools immediately
_register_web_research_tools()

# Add model escalation tools if available (lazy import)
def _register_model_escalation_tools():
    """Register model escalation tools in TOOL_REGISTRY"""
    try:
        from tools.model_escalation import ModelEscalationTools as MET
        TOOL_REGISTRY.update({
            "escalate_to_flagship": {
                "function": MET.escalate_to_flagship,
                "description": "Escalate complex task to flagship model (DeepSeek, GPT-4, Claude). Use when task is too complex. Security: requires API key, rate-limited to prevent cost overruns"
            },
            "check_complexity": {
                "function": MET.check_complexity,
                "description": "Check if task is too complex for current model. Returns complexity assessment and recommendation"
            },
            "get_flagship_help": {
                "function": MET.get_flagship_help,
                "description": "Get help from flagship model for specific issue. Simpler interface than escalate_to_flagship"
            },
            "refine_with_flagship": {
                "function": MET.refine_with_flagship,
                "description": "Refine solution using flagship model. Provides improved version based on feedback"
            }
        })
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register model escalation tools immediately
_register_model_escalation_tools()

# =============================================================================
# CONSOLIDATED TOOLS REGISTRATION (Phase 2)
# Register all 26 consolidated tools that replace the original 97 tools
# =============================================================================

def _register_consolidated_tools():
    """Register consolidated tools in TOOL_REGISTRY"""
    try:
        from tools.consolidated import TOOL_REGISTRY_CONSOLIDATED
        # Register all consolidated tools
        TOOL_REGISTRY.update(TOOL_REGISTRY_CONSOLIDATED)
        return True
    except (ImportError, AttributeError) as e:
        return False

# Register consolidated tools immediately
_register_consolidated_tools()

# =============================================================================
# MIGRATION SUPPORT (Phase 3)
# Provide backward compatibility by automatically migrating old tool calls
# =============================================================================

def _migrate_tool_if_needed(tool_name: str, **kwargs) -> tuple[str, dict]:
    """
    Migrate old tool name to new consolidated tool if needed.
    
    Args:
        tool_name: Tool name (old or new)
        **kwargs: Tool arguments
    
    Returns:
        Tuple of (tool_name, kwargs) - possibly migrated
    """
    try:
        from tools.consolidated.migration import migrate_tool_call, is_old_tool
        
        # Check if this is an old tool
        if is_old_tool(tool_name):
            # Migrate to new tool
            new_name, new_kwargs = migrate_tool_call(tool_name, **kwargs)
            return new_name, new_kwargs
        
        # Already a new tool or not in migration mapping
        return tool_name, kwargs
    except (ImportError, AttributeError):
        # Migration layer not available - return as-is
        return tool_name, kwargs

# Helper function to get tool with automatic migration
def get_tool(tool_name: str):
    """
    Get tool function with automatic migration from old to new tools.
    
    Args:
        tool_name: Tool name (old or new)
    
    Returns:
        Tool function or None if not found
    """
    # Try to migrate first
    migrated_name, _ = _migrate_tool_if_needed(tool_name)
    
    # Get tool from registry
    if migrated_name in TOOL_REGISTRY:
        return TOOL_REGISTRY[migrated_name]["function"]
    
    # Fallback: check original name
    if tool_name in TOOL_REGISTRY:
        return TOOL_REGISTRY[tool_name]["function"]
    
    return None