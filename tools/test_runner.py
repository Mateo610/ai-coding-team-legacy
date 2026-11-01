"""
Test Runner tools for agents to run tests across different frameworks
"""
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from tools.code_tools import ToolResult
from tools.file_tools import FileTools
from agents.timeout_config import TIMEOUT_CONFIG


class TestRunnerTools:
    """Tools for running tests across different frameworks"""
    
    @staticmethod
    def _is_safe_path(filepath: str) -> tuple[bool, Optional[str]]:
        """Check if filepath is safe to access (delegates to FileTools)"""
        return FileTools._is_safe_path(filepath)
    
    @staticmethod
    def _detect_test_framework(path: Path) -> str:
        """Auto-detect test framework from project structure"""
        # Check for pytest (Python)
        if (path / "pytest.ini").exists() or (path / "pyproject.toml").exists():
            try:
                pyproject = (path / "pyproject.toml").read_text(encoding='utf-8', errors='ignore')
                if "pytest" in pyproject.lower():
                    return "pytest"
            except:
                pass
        
        # Check for package.json (JavaScript/TypeScript)
        package_json = path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})
                    
                    # Check for test scripts
                    if "test" in scripts:
                        test_script = scripts["test"].lower()
                        if "vitest" in test_script:
                            return "vitest"
                        elif "jest" in test_script:
                            return "jest"
                        else:
                            return "npm_test"
            except:
                pass
        
        # Check for test directories/files
        if (path / "tests").exists() or (path / "test").exists():
            # Check if Python tests
            test_files = list(path.glob("test_*.py")) + list(path.glob("*_test.py"))
            if test_files:
                return "pytest"
            
            # Check if JavaScript tests
            test_files = list(path.glob("*.test.js")) + list(path.glob("*.spec.js"))
            if test_files:
                return "npm_test"
        
        # Default to pytest for Python projects
        if (path / "requirements.txt").exists() or (path / "setup.py").exists():
            return "pytest"
        
        return "unknown"
    
    @staticmethod
    def run_tests(
        test_path: str = "tests",
        framework: str = "auto",
        path: str = ".",
        timeout: int = None
    ) -> ToolResult:
        """
        Run tests and return summary.
        
        Args:
            test_path: Path to tests (default: "tests")
            framework: Test framework ("auto", "pytest", "npm_test", "vitest")
            path: Project path (default: current directory)
            timeout: Timeout in seconds (default: from config)
        
        Returns:
            ToolResult with test results summary
        """
        try:
            # Validate path
            is_safe, error = TestRunnerTools._is_safe_path(path)
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
            
            # Auto-detect framework if needed
            if framework == "auto":
                framework = TestRunnerTools._detect_test_framework(project_path)
                if framework == "unknown":
                    return ToolResult(
                        success=False,
                        result=None,
                        error="Could not auto-detect test framework. Please specify framework."
                    )
            
            # Get timeout
            if timeout is None:
                timeout = TIMEOUT_CONFIG.get_code_execution_timeout() * 3  # Longer timeout for tests
            
            # Run tests based on framework
            if framework == "pytest":
                return TestRunnerTools.run_pytest(test_path, project_path, timeout)
            elif framework == "npm_test":
                return TestRunnerTools.run_npm_test(project_path, timeout)
            elif framework == "vitest":
                return TestRunnerTools.run_vitest(project_path, timeout)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unsupported test framework: {framework}"
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running tests: {str(e)}"
            )
    
    @staticmethod
    def run_pytest(test_path: str, project_path: Path, timeout: int) -> ToolResult:
        """Run pytest tests"""
        try:
            # Build pytest command
            pytest_cmd = ["python3", "-m", "pytest", test_path, "-v", "--tb=short"]
            
            # Run pytest
            result = subprocess.run(
                pytest_cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Parse output
            output = result.stdout + result.stderr
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            errors = output.count(' ERROR')
            total = passed + failed + errors
            
            # Extract failing test names
            failing_tests = []
            for line in output.split('\n'):
                if ' FAILED' in line:
                    # Extract test name
                    match = re.search(r'(\w+::\w+)', line)
                    if match:
                        failing_tests.append(match.group(1))
                    else:
                        # Try alternative pattern
                        match = re.search(r'(test_\w+)', line)
                        if match:
                            failing_tests.append(match.group(1))
            
            # Extract error snippets
            error_snippets = []
            if failed > 0 or errors > 0:
                # Find error sections
                lines = output.split('\n')
                in_error = False
                error_lines = []
                for line in lines:
                    if 'FAILED' in line or 'ERROR' in line:
                        in_error = True
                        error_lines = [line]
                    elif in_error:
                        error_lines.append(line)
                        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                            # End of error block
                            if len(error_lines) <= 10:  # Limit error snippet size
                                error_snippets.append('\n'.join(error_lines))
                            in_error = False
                            error_lines = []
                
                # Add last error if still in error block
                if error_lines and len(error_lines) <= 10:
                    error_snippets.append('\n'.join(error_lines))
            
            return ToolResult(
                success=result.returncode == 0 and failed == 0,
                result={
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "total": total,
                    "failing_tests": failing_tests[:10],  # Limit to 10
                    "error_snippets": error_snippets[:5],  # Limit to 5
                    "output": output[-1000:],  # Last 1000 chars
                    "framework": "pytest"
                },
                error=output if result.returncode != 0 else "",
                metadata={
                    "path": str(project_path),
                    "test_path": test_path,
                    "framework": "pytest",
                    "passed": passed,
                    "failed": failed,
                    "total": total
                }
            )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tests timed out after {timeout}s"
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                result=None,
                error="pytest not found. Install with: pip install pytest"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running pytest: {str(e)}"
            )
    
    @staticmethod
    def run_npm_test(project_path: Path, timeout: int) -> ToolResult:
        """Run npm test"""
        try:
            # Check if package.json exists
            package_json = project_path / "package.json"
            if not package_json.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error="package.json not found"
                )
            
            # Run npm test
            result = subprocess.run(
                ["npm", "test"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Try to extract test results (format varies by test framework)
            passed = output.count('passed') + output.count('PASS')
            failed = output.count('failed') + output.count('FAIL')
            total = passed + failed
            
            # Extract failing test names
            failing_tests = []
            for line in output.split('\n'):
                if 'FAIL' in line or 'failed' in line:
                    # Extract test name
                    match = re.search(r'(\w+)', line)
                    if match:
                        failing_tests.append(match.group(1))
            
            return ToolResult(
                success=result.returncode == 0 and failed == 0,
                result={
                    "passed": passed,
                    "failed": failed,
                    "total": total,
                    "failing_tests": failing_tests[:10],
                    "output": output[-1000:],
                    "framework": "npm_test"
                },
                error=output if result.returncode != 0 else "",
                metadata={
                    "path": str(project_path),
                    "framework": "npm_test",
                    "passed": passed,
                    "failed": failed,
                    "total": total
                }
            )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tests timed out after {timeout}s"
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                result=None,
                error="npm not found. Is Node.js installed?"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running npm test: {str(e)}"
            )
    
    @staticmethod
    def run_vitest(project_path: Path, timeout: int) -> ToolResult:
        """Run vitest tests"""
        try:
            # Check if package.json exists
            package_json = project_path / "package.json"
            if not package_json.exists():
                return ToolResult(
                    success=False,
                    result=None,
                    error="package.json not found"
                )
            
            # Run vitest
            result = subprocess.run(
                ["npx", "vitest", "run"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Extract test results (vitest format)
            passed_match = re.search(r'(\d+)\s+passed', output)
            failed_match = re.search(r'(\d+)\s+failed', output)
            
            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            total = passed + failed
            
            # Extract failing test names
            failing_tests = []
            for line in output.split('\n'):
                if 'FAIL' in line or 'failed' in line:
                    match = re.search(r'(\w+)', line)
                    if match:
                        failing_tests.append(match.group(1))
            
            return ToolResult(
                success=result.returncode == 0 and failed == 0,
                result={
                    "passed": passed,
                    "failed": failed,
                    "total": total,
                    "failing_tests": failing_tests[:10],
                    "output": output[-1000:],
                    "framework": "vitest"
                },
                error=output if result.returncode != 0 else "",
                metadata={
                    "path": str(project_path),
                    "framework": "vitest",
                    "passed": passed,
                    "failed": failed,
                    "total": total
                }
            )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tests timed out after {timeout}s"
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                result=None,
                error="npx not found. Is Node.js installed?"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error running vitest: {str(e)}"
            )
    
    @staticmethod
    def get_test_summary(results: Dict) -> ToolResult:
        """
        Parse test results and return structured summary.
        
        Args:
            results: Test results dictionary
        
        Returns:
            ToolResult with structured summary
        """
        try:
            if not results:
                return ToolResult(
                    success=False,
                    result=None,
                    error="No test results provided"
                )
            
            passed = results.get("passed", 0)
            failed = results.get("failed", 0)
            total = results.get("total", passed + failed)
            
            # Calculate pass rate
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            summary = {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{pass_rate:.1f}%",
                "status": "PASS" if failed == 0 else "FAIL",
                "failing_tests": results.get("failing_tests", []),
                "framework": results.get("framework", "unknown")
            }
            
            return ToolResult(
                success=failed == 0,
                result=summary,
                metadata={
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": pass_rate
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error parsing test summary: {str(e)}"
            )

