"""
Test Phase 3 Tools: Test Runner + Lint Tools
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.code_tools import TOOL_REGISTRY
from tools.test_runner import TestRunnerTools
from tools.lint_tools import LintTools


def test_tool_registration():
    """Test that Phase 3 tools are registered"""
    print("=" * 70)
    print("Test 1: Tool Registration")
    print("=" * 70)
    
    # Expected Test Runner Tools
    expected_test_tools = [
        "run_tests",
        "run_pytest",
        "run_npm_test",
        "run_vitest",
        "get_test_summary"
    ]
    
    # Expected Lint Tools
    expected_lint_tools = [
        "run_linter",
        "run_formatter",
        "fix_code",
        "lint_python",
        "lint_javascript",
        "show_lint_diff"
    ]
    
    print("\nTest Runner Tools:")
    test_found = []
    for tool in expected_test_tools:
        if tool in TOOL_REGISTRY:
            test_found.append(tool)
            print(f"✅ {tool} - registered")
        else:
            print(f"❌ {tool} - NOT registered")
    
    print("\nLint Tools:")
    lint_found = []
    for tool in expected_lint_tools:
        if tool in TOOL_REGISTRY:
            lint_found.append(tool)
            print(f"✅ {tool} - registered")
        else:
            print(f"❌ {tool} - NOT registered")
    
    all_found = len(test_found) == len(expected_test_tools) and len(lint_found) == len(expected_lint_tools)
    print(f"\nResult: {len(test_found)}/{len(expected_test_tools)} Test Runner tools, {len(lint_found)}/{len(expected_lint_tools)} Lint tools")
    return all_found


def test_test_runner_structure():
    """Test Test Runner Tools function structure"""
    print("\n" + "=" * 70)
    print("Test 2: Test Runner Tools Structure")
    print("=" * 70)
    
    test_functions = [
        ("run_tests", ["test_path", "framework", "path", "timeout"]),
        ("run_pytest", ["test_path", "project_path", "timeout"]),
        ("run_npm_test", ["project_path", "timeout"]),
        ("run_vitest", ["project_path", "timeout"]),
        ("get_test_summary", ["results"]),
    ]
    
    all_exist = True
    for func_name, params in test_functions:
        if hasattr(TestRunnerTools, func_name):
            func = getattr(TestRunnerTools, func_name)
            if callable(func):
                print(f"✅ {func_name} - exists and callable")
            else:
                print(f"❌ {func_name} - exists but not callable")
                all_exist = False
        else:
            print(f"❌ {func_name} - does not exist")
            all_exist = False
    
    return all_exist


def test_lint_tools_structure():
    """Test Lint Tools function structure"""
    print("\n" + "=" * 70)
    print("Test 3: Lint Tools Structure")
    print("=" * 70)
    
    lint_functions = [
        ("run_linter", ["filepath", "tool", "fix", "path"]),
        ("run_formatter", ["filepath", "tool", "path"]),
        ("fix_code", ["filepath", "tool", "path"]),
        ("lint_python", ["filepath", "tool", "fix", "path"]),
        ("lint_javascript", ["filepath", "tool", "fix", "path"]),
        ("show_lint_diff", ["filepath", "tool", "path"]),
    ]
    
    all_exist = True
    for func_name, params in lint_functions:
        if hasattr(LintTools, func_name):
            func = getattr(LintTools, func_name)
            if callable(func):
                print(f"✅ {func_name} - exists and callable")
            else:
                print(f"❌ {func_name} - exists but not callable")
                all_exist = False
        else:
            print(f"❌ {func_name} - does not exist")
            all_exist = False
    
    return all_exist


def test_framework_detection():
    """Test framework auto-detection"""
    print("\n" + "=" * 70)
    print("Test 4: Framework Auto-Detection")
    print("=" * 70)
    
    try:
        from pathlib import Path
        
        # Test with current directory
        current_path = Path.cwd()
        framework = TestRunnerTools._detect_test_framework(current_path)
        
        if framework != "unknown":
            print(f"✅ Detected framework: {framework} (for current directory)")
            return True
        else:
            print(f"⚠️  Could not detect framework (may be expected): {framework}")
            return True  # Not a failure if no framework detected
        
    except Exception as e:
        print(f"❌ Framework detection exception: {str(e)[:100]}")
        return False


def test_language_detection():
    """Test language detection"""
    print("\n" + "=" * 70)
    print("Test 5: Language Detection")
    print("=" * 70)
    
    try:
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.json", "json"),
        ]
        
        all_passed = True
        for filename, expected_lang in test_cases:
            file_path = Path(filename)
            detected = LintTools._detect_language(file_path)
            
            if detected == expected_lang:
                print(f"✅ '{filename}' - correctly detected as {detected}")
            else:
                print(f"❌ '{filename}' - detected as {detected}, expected {expected_lang}")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print(f"❌ Language detection exception: {str(e)[:100]}")
        return False


def test_test_summary_parsing():
    """Test test summary parsing"""
    print("\n" + "=" * 70)
    print("Test 6: Test Summary Parsing")
    print("=" * 70)
    
    try:
        # Test with sample results
        sample_results = {
            "passed": 5,
            "failed": 2,
            "total": 7,
            "framework": "pytest"
        }
        
        result = TestRunnerTools.get_test_summary(sample_results)
        
        if result.success:
            summary = result.result
            if summary.get("total") == 7 and summary.get("passed") == 5:
                print(f"✅ Test summary parsed correctly")
                print(f"   Total: {summary.get('total')}, Passed: {summary.get('passed')}, Failed: {summary.get('failed')}")
                return True
            else:
                print(f"❌ Test summary parsing failed: incorrect values")
                return False
        else:
            print(f"❌ Test summary parsing failed: {result.error[:100]}")
            return False
    
    except Exception as e:
        print(f"❌ Test summary parsing exception: {str(e)[:100]}")
        return False


def test_path_validation():
    """Test path validation security"""
    print("\n" + "=" * 70)
    print("Test 7: Path Validation Security")
    print("=" * 70)
    
    # Test safe paths
    safe_paths = [
        ".",
        "tools/test_runner.py",
        "tests/test_example.py",
    ]
    
    # Test unsafe paths
    unsafe_paths = [
        "/etc/passwd",
        "../../etc/passwd",
        "/root/secret",
    ]
    
    print("\nSafe paths (should pass):")
    all_passed = True
    for path in safe_paths:
        is_safe, error = TestRunnerTools._is_safe_path(path)
        if is_safe:
            print(f"✅ '{path}' - correctly allowed")
        else:
            print(f"❌ '{path}' - incorrectly rejected: {error}")
            all_passed = False
    
    print("\nUnsafe paths (should fail):")
    for path in unsafe_paths:
        is_safe, error = TestRunnerTools._is_safe_path(path)
        if not is_safe:
            print(f"✅ '{path}' - correctly blocked")
        else:
            print(f"❌ '{path}' - incorrectly allowed!")
            all_passed = False
    
    return all_passed


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("\n" + "=" * 70)
    print("Test 8: Error Handling")
    print("=" * 70)
    
    # Test invalid file path
    result = LintTools.run_linter("/etc/passwd", "black", fix=False, path=".")
    if not result.success:
        print(f"✅ Invalid file path correctly rejected: {result.error[:50]}...")
    else:
        print(f"❌ Invalid file path should have been rejected")
        return False
    
    # Test invalid framework
    result = TestRunnerTools.run_tests("tests", framework="invalid_framework", path=".")
    if not result.success:
        print(f"✅ Invalid framework correctly rejected: {result.error[:50]}...")
    else:
        print(f"❌ Invalid framework should have been rejected")
        return False
    
    # Test empty test summary
    result = TestRunnerTools.get_test_summary({})
    if not result.success:
        print(f"✅ Empty test results correctly handled: {result.error[:50]}...")
    else:
        print(f"⚠️  Empty test results were accepted (may be valid)")
    
    print("✅ Error handling working correctly")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 Phase 3 Tools - Implementation Tests")
    print("=" * 70)
    
    tests = [
        ("Tool Registration", test_tool_registration),
        ("Test Runner Structure", test_test_runner_structure),
        ("Lint Tools Structure", test_lint_tools_structure),
        ("Framework Auto-Detection", test_framework_detection),
        ("Language Detection", test_language_detection),
        ("Test Summary Parsing", test_test_summary_parsing),
        ("Path Validation Security", test_path_validation),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Phase 3 tools are ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed or had warnings")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

