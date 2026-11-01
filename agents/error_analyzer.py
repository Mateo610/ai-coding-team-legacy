"""
Error Analyzer - analyzes test failures and generates fix suggestions
"""

from typing import Dict, List, Any
import re


class ErrorAnalyzer:
    """Analyzes test failures and extracts actionable error information"""

    def analyze(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze validation results to extract error information
        
        Returns:
            {
                'has_errors': bool,
                'error_type': str,  # 'syntax', 'runtime', 'test_failure', 'import', etc.
                'error_summary': str,
                'specific_errors': List[str],
                'fix_suggestions': str,
                'code_locations': List[Dict[str, Any]]  # Line numbers, functions, etc.
            }
        """
        analysis = {
            'has_errors': False,
            'error_type': None,
            'error_summary': '',
            'specific_errors': [],
            'fix_suggestions': '',
            'code_locations': []
        }

        # Check syntax errors
        syntax_check = validation_results.get('syntax_check', {})
        if not syntax_check.get('success', True):
            analysis['has_errors'] = True
            analysis['error_type'] = 'syntax'
            error_msg = syntax_check.get('error', '')
            analysis['error_summary'] = f"Syntax error: {error_msg}"
            analysis['specific_errors'].append(error_msg)
            analysis['fix_suggestions'] = self._suggest_syntax_fixes(error_msg)
            return analysis

        # Check test execution errors
        tests_run = validation_results.get('tests_run', {})
        if not tests_run.get('success', False):
            metadata = tests_run.get('metadata', {})
            error_msg = tests_run.get('error', '')
            
            analysis['has_errors'] = True
            
            # Determine error type
            if metadata.get('pytest_missing'):
                analysis['error_type'] = 'pytest_missing'
                analysis['error_summary'] = "pytest is not installed"
                analysis['fix_suggestions'] = "Install pytest with: pip install pytest"
                return analysis
            
            if metadata.get('syntax_error'):
                analysis['error_type'] = 'syntax'
                analysis['error_summary'] = "Syntax error in test code"
                analysis['specific_errors'].append(error_msg)
                analysis['fix_suggestions'] = self._suggest_syntax_fixes(error_msg)
                return analysis
            
            if metadata.get('collection_error') or metadata.get('no_tests'):
                analysis['error_type'] = 'test_collection'
                analysis['error_summary'] = "Tests could not be collected"
                analysis['specific_errors'].append(error_msg)
                analysis['fix_suggestions'] = self._suggest_collection_fixes(error_msg)
                return analysis
            
            # Test failures (tests ran but failed)
            failed = metadata.get('failed', 0)
            if failed > 0:
                analysis['error_type'] = 'test_failure'
                passed = metadata.get('passed', 0)
                total = metadata.get('total', 0)
                analysis['error_summary'] = f"Tests failed: {failed}/{total} tests failed, {passed} passed"
                
                # Parse specific test failures from error output
                full_output = metadata.get('full_output', error_msg) or ""
                test_errors = self._parse_test_failures(full_output)
                analysis['specific_errors'].extend(test_errors)
                analysis['fix_suggestions'] = self._suggest_test_failure_fixes(test_errors)
                analysis['code_locations'] = self._extract_code_locations(full_output)
                
                return analysis

        # Check execution errors
        execution = validation_results.get('execution', {})
        if execution and not execution.get('success', True):
            error_msg = execution.get('error', '')
            if error_msg and 'skipped' not in error_msg.lower():
                analysis['has_errors'] = True
                analysis['error_type'] = 'runtime'
                analysis['error_summary'] = f"Runtime error: {error_msg[:200]}"
                analysis['specific_errors'].append(error_msg)
                analysis['fix_suggestions'] = self._suggest_runtime_fixes(error_msg)
                return analysis

        return analysis

    def _parse_test_failures(self, output: str) -> List[str]:
        """Parse individual test failures from pytest output with more detail"""
        errors = []
        if not output:
            return errors
        lines = output.split('\n')
        
        # Look for FAILED test markers
        for i, line in enumerate(lines):
            if ' FAILED' in line or 'ERROR' in line:
                # Get test name
                test_name = line.split('::')[-1].strip() if '::' in line else ''
                
                # Get more comprehensive error details
                error_lines = []
                in_error_block = False
                
                for j in range(i+1, min(i+30, len(lines))):  # Look further ahead
                    current_line = lines[j]
                    stripped = current_line.strip()
                    
                    # Stop at next test or section divider
                    if (stripped.startswith('=') and len(stripped) > 10) or ' PASSED' in current_line:
                        break
                    
                    # Collect error details (skip empty lines at start)
                    if stripped or in_error_block:
                        in_error_block = True
                        # Skip traceback file paths but keep error messages
                        if not (stripped.startswith('File ') and '.py' in stripped and 'line' in stripped):
                            error_lines.append(stripped)
                        
                        # Stop after collecting error message (usually ends with specific error)
                        if any(keyword in stripped for keyword in ['AssertionError', 'TypeError', 'ValueError', 'AttributeError', 'KeyError']):
                            # Get next line if it has the actual error detail
                            if j + 1 < len(lines):
                                next_line = lines[j + 1].strip()
                                if next_line and not next_line.startswith('File '):
                                    error_lines.append(next_line)
                            break
                
                error_detail = ' | '.join([line for line in error_lines[:5] if line])  # First 5 non-empty lines
                if error_detail:
                    errors.append(f"{test_name}: {error_detail}")
        
        # Also look for AssertionError messages with more context
        for i, line in enumerate(lines):
            if 'AssertionError' in line:
                # Extract the assertion message
                match = re.search(r'AssertionError:\s*(.+)', line)
                if match:
                    error_msg = match.group(1).strip()
                    # Get next line which often has the comparison detail
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith('File '):
                            error_msg += f" | {next_line}"
                    errors.append(f"Assertion failed: {error_msg[:150]}")
        
        # Extract specific error types for better categorization
        error_type_counts = {}
        for error in errors:
            for error_type in ['AssertionError', 'TypeError', 'ValueError', 'AttributeError', 'KeyError', 'IndexError']:
                if error_type in error:
                    error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
                    break
        
        # Add summary if multiple errors of same type
        if error_type_counts:
            summary = " | ".join([f"{count}x {err_type}" for err_type, count in error_type_counts.items() if count > 1])
            if summary:
                errors.insert(0, f"Error summary: {summary}")
        
        return errors[:7]  # Limit to 7 most relevant errors (increased from 5)

    def _extract_code_locations(self, output: str) -> List[Dict[str, Any]]:
        """Extract file locations and line numbers from errors"""
        locations = []
        
        # Look for file paths and line numbers
        pattern = r'(?:File |at )(?:.*?/)?([^/]+\.py)["\'].*?line (\d+)'
        matches = re.findall(pattern, output)
        
        for filename, line_num in matches:
            locations.append({
                'file': filename,
                'line': int(line_num) if line_num.isdigit() else None
            })
        
        return locations[:3]  # Limit to 3 locations

    def _suggest_syntax_fixes(self, error_msg: str) -> str:
        """Generate syntax error fix suggestions"""
        suggestions = []
        
        if 'unexpected EOF' in error_msg or 'expected an indented block' in error_msg:
            suggestions.append("- Check for missing closing brackets, parentheses, or colons")
            suggestions.append("- Ensure all function/class definitions have bodies")
        
        if 'invalid syntax' in error_msg:
            suggestions.append("- Check for typos in keywords (def, class, if, etc.)")
            suggestions.append("- Verify all quotes are properly closed")
        
        if 'indentation' in error_msg.lower():
            suggestions.append("- Fix indentation (use consistent spaces or tabs)")
            suggestions.append("- Ensure proper indentation after colons")
        
        if 'NameError' in error_msg:
            suggestions.append("- Define the variable before using it")
            suggestions.append("- Check for typos in variable names")
        
        if not suggestions:
            suggestions.append("- Review the syntax error message carefully")
            suggestions.append("- Check the line number mentioned in the error")
        
        return "\n".join(suggestions)

    def _suggest_collection_fixes(self, error_msg: str) -> str:
        """Generate test collection error fix suggestions"""
        suggestions = [
            "- Ensure test functions start with 'test_'",
            "- Check that test file has valid Python syntax",
            "- Verify imports are correct and modules are available",
            "- Make sure test functions are defined at module level (not inside other functions)"
        ]
        return "\n".join(suggestions)

    def _suggest_test_failure_fixes(self, test_errors: List[str]) -> str:
        """Generate comprehensive test failure fix suggestions with code examples"""
        suggestions = []
        code_examples = []
        
        for error in test_errors:
            error_lower = error.lower()
            
            if 'AssertionError' in error:
                if '== ' in error or '!=' in error or 'not equal' in error_lower:
                    suggestions.append("- Fix the comparison logic or expected values")
                    suggestions.append("- Check that the function returns the correct type")
                    # Extract actual vs expected if possible
                    if 'assert' in error_lower:
                        suggestions.append("- Verify the assertion matches the function's actual behavior")
                    code_examples.append("""
# Example fix for AssertionError:
# Before: assert result == 5
# After: Check what function actually returns, then fix:
result = function_name(2, 3)
assert result == actual_expected_value  # Use correct expected value
""")
                
            if 'TypeError' in error:
                suggestions.append("- Fix type mismatches (e.g., string vs int)")
                suggestions.append("- Add type conversions where needed")
                suggestions.append("- Check function parameter types match what's being passed")
                code_examples.append("""
# Example fix for TypeError:
# Before: result = add("2", 3)  # String + int
# After: Convert types or fix function signature:
result = add(2, 3)  # Both ints
# OR modify function to handle different types
""")
            
            if 'AttributeError' in error:
                suggestions.append("- Check if the object has the expected attribute/method")
                suggestions.append("- Verify the object type matches expectations")
                suggestions.append("- Ensure object is initialized before accessing attributes")
                code_examples.append("""
# Example fix for AttributeError:
# Before: user.name  # user might be None or wrong type
# After: Check object type first:
if user and hasattr(user, 'name'):
    result = user.name
# OR ensure user is properly initialized
""")
            
            if 'KeyError' in error or 'IndexError' in error:
                suggestions.append("- Handle missing keys/indices or add default values")
                suggestions.append("- Validate dictionary/list has the key/index before accessing")
                code_examples.append("""
# Example fix for KeyError/IndexError:
# Before: value = data['key']  # key might not exist
# After: Use .get() with default or check first:
value = data.get('key', default_value)
# OR: if 'key' in data: value = data['key']
""")
            
            if 'ValueError' in error:
                suggestions.append("- Validate inputs and handle invalid values")
                suggestions.append("- Add input validation at the beginning of the function")
                code_examples.append("""
# Example fix for ValueError:
# Before: def divide(a, b): return a / b  # No validation
# After: Add validation:
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
            
            if 'NameError' in error:
                suggestions.append("- Define missing variables or import missing modules")
                suggestions.append("- Check for typos in variable/function names")
            
            if 'ImportError' in error or 'ModuleNotFoundError' in error:
                suggestions.append("- Install missing dependencies: pip install <package>")
                suggestions.append("- Fix import paths or check if module exists")
        
        if not suggestions:
            suggestions.append("- Review the test failure messages carefully")
            suggestions.append("- Check that function logic matches expected behavior")
            suggestions.append("- Verify edge cases are handled correctly")
            suggestions.append("- Add print statements to debug what the function actually returns")
        
        # Combine suggestions with code examples
        result = "\n".join(suggestions)
        if code_examples:
            result += "\n\nCODE EXAMPLES:\n" + "\n".join(code_examples[:3])  # Limit to 3 examples
        
        # Deduplicate while preserving order
        return "\n".join(list(dict.fromkeys(result.split('\n'))))

    def _suggest_runtime_fixes(self, error_msg: str) -> str:
        """Generate runtime error fix suggestions"""
        suggestions = []
        
        if 'TypeError' in error_msg:
            suggestions.append("- Fix type mismatches in function calls")
            suggestions.append("- Add type conversions or fix parameter types")
        
        if 'NameError' in error_msg:
            suggestions.append("- Define missing variables or import missing modules")
        
        if 'AttributeError' in error_msg:
            suggestions.append("- Check object type and available methods/attributes")
        
        if 'ImportError' in error_msg or 'ModuleNotFoundError' in error_msg:
            suggestions.append("- Install missing dependencies or fix import paths")
        
        if not suggestions:
            suggestions.append("- Review the runtime error message")
            suggestions.append("- Add error handling for edge cases")
        
        return "\n".join(suggestions)

    def generate_fix_prompt(self, analysis: Dict[str, Any], code: str, original_task: str, task_type: str = "general") -> str:
        """
        Generate an improved task prompt with error context for re-generation
        
        Args:
            analysis: Error analysis dictionary
            code: Generated code that failed
            original_task: Original task description
            task_type: Task type for context (default: "general")
        
        Returns a new task string that includes error information
        """
        if not analysis['has_errors']:
            return original_task
        
        error_context = f"""\n\n=== PREVIOUS ATTEMPT FAILED ===
Error Type: {analysis['error_type']}
Error Summary: {analysis['error_summary']}

Specific Errors:
{chr(10).join('- ' + err for err in analysis['specific_errors'][:3])}

Fix Suggestions:
{analysis['fix_suggestions']}
"""

        if analysis['code_locations']:
            locations_str = "\n".join(
                f"- {loc['file']}, line {loc['line']}" 
                for loc in analysis['code_locations']
            )
            error_context += f"\nCode Locations to Fix:\n{locations_str}\n"

        fix_task = f"""{original_task}

{error_context}

IMPORTANT: Fix the above errors in your implementation. Review the error messages carefully and ensure your code addresses all the issues mentioned."""
        
        return fix_task

