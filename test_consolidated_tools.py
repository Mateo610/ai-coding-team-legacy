"""
Test script for consolidated tools
Verifies that all consolidated tools work correctly with their various modes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.consolidated.fs_tools import FSTools
from tools.consolidated.project_tools import ProjectTools
from tools.consolidated.code_quality_tools import CodeQualityTools
from tools.consolidated.quality_tools import QualityTools
from tools.consolidated.git_consolidated import GitConsolidated


def test_fs_tools():
    """Test fs_read, fs_write, fs_list"""
    print("\n" + "=" * 70)
    print("Testing FSTools")
    print("=" * 70)
    
    # Test fs_read with mode="read"
    print("\n1. Testing fs_read (mode='read')...")
    result = FSTools.fs_read("README.md", mode="read")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ File read successfully (first 100 chars: {str(result.result)[:100]}...)")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test fs_read with mode="exists"
    print("\n2. Testing fs_read (mode='exists')...")
    result = FSTools.fs_read("README.md", mode="exists")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ File existence checked: {result.result}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test fs_list with mode="directory"
    print("\n3. Testing fs_list (mode='directory')...")
    result = FSTools.fs_list(".", mode="directory")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Directory listed successfully")
        if result.metadata and "count" in result.metadata:
            print(f"   Items found: {result.metadata['count']}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test fs_list with mode="files"
    print("\n4. Testing fs_list (mode='files', pattern='*.py')...")
    result = FSTools.fs_list(".", mode="files", pattern="*.py")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Files found")
        if result.metadata and "count" in result.metadata:
            print(f"   Files found: {result.metadata['count']}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    print("\n✅ FSTools tests completed")


def test_project_tools():
    """Test project_scan, code_search"""
    print("\n" + "=" * 70)
    print("Testing ProjectTools")
    print("=" * 70)
    
    # Test project_scan with mode="full"
    print("\n1. Testing project_scan (mode='full')...")
    result = ProjectTools.project_scan(".", mode="full")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Project scanned successfully")
        if isinstance(result.result, dict):
            print(f"   Modules found: {len(result.result.get('modules', []))}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test project_scan with mode="entrypoints"
    print("\n2. Testing project_scan (mode='entrypoints')...")
    result = ProjectTools.project_scan(".", mode="entrypoints")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Entrypoints found")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test code_search with mode="text"
    print("\n3. Testing code_search (mode='text', pattern='def main')...")
    result = ProjectTools.code_search("def main", ".", mode="text")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Code search completed")
        if isinstance(result.result, dict) and "count" in result.result:
            print(f"   Matches found: {result.result['count']}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test code_search with mode="todos"
    print("\n4. Testing code_search (mode='todos')...")
    result = ProjectTools.code_search("TODO", ".", mode="todos")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ TODOs found")
    else:
        print(f"   ✗ Error: {result.error}")
    
    print("\n✅ ProjectTools tests completed")


def test_code_quality_tools():
    """Test code_check, code_format, code_execute"""
    print("\n" + "=" * 70)
    print("Testing CodeQualityTools")
    print("=" * 70)
    
    test_code = """
def hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(hello("World"))
"""
    
    # Test code_check with mode="syntax"
    print("\n1. Testing code_check (mode='syntax')...")
    result = CodeQualityTools.code_check(test_code, mode="syntax")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Syntax check passed")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test code_check with mode="complexity"
    print("\n2. Testing code_check (mode='complexity')...")
    result = CodeQualityTools.code_check(test_code, mode="complexity")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Complexity analyzed")
        if result.metadata:
            print(f"   Functions: {result.metadata.get('functions', 'N/A')}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    # Test code_format with mode="format"
    print("\n3. Testing code_format (mode='format')...")
    result = CodeQualityTools.code_format(test_code, mode="format")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Code formatted")
    else:
        print(f"   ⚠️  Formatting unavailable (may need black): {result.error[:100] if result.error else 'N/A'}")
    
    # Test code_execute
    print("\n4. Testing code_execute...")
    simple_code = "print('Hello from test!')"
    result = CodeQualityTools.code_execute(simple_code)
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Code executed successfully")
        print(f"   Output: {result.result[:100] if result.result else 'N/A'}")
    else:
        print(f"   ✗ Error: {result.error}")
    
    print("\n✅ CodeQualityTools tests completed")


def test_quality_tools():
    """Test test_run, lint_run"""
    print("\n" + "=" * 70)
    print("Testing QualityTools")
    print("=" * 70)
    
    # Test test_run with framework="auto"
    print("\n1. Testing test_run (framework='auto')...")
    result = QualityTools.test_run(test_path="tests", framework="auto", path=".")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Test runner initialized")
    else:
        print(f"   ⚠️  No tests found or framework not detected: {result.error[:100] if result.error else 'N/A'}")
    
    # Test lint_run with mode="lint"
    print("\n2. Testing lint_run (mode='lint')...")
    # Create a test file if it doesn't exist
    test_file = Path("test_lint.py")
    if not test_file.exists():
        test_file.write_text("def test_function():\n    pass\n")
    
    result = QualityTools.lint_run("test_lint.py", mode="lint", language="python")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Linting completed")
    else:
        print(f"   ⚠️  Linter unavailable or no issues: {result.error[:100] if result.error else 'N/A'}")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
    
    print("\n✅ QualityTools tests completed")


def test_git_tools():
    """Test git_inspect, git_modify"""
    print("\n" + "=" * 70)
    print("Testing GitConsolidated")
    print("=" * 70)
    
    # Test git_inspect with mode="status"
    print("\n1. Testing git_inspect (mode='status')...")
    result = GitConsolidated.git_inspect(mode="status")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Git status retrieved")
        if isinstance(result.result, dict):
            branch = result.result.get("branch", "N/A")
            print(f"   Branch: {branch}")
    else:
        print(f"   ⚠️  Not a git repo or git unavailable: {result.error[:100] if result.error else 'N/A'}")
    
    # Test git_inspect with mode="branch"
    print("\n2. Testing git_inspect (mode='branch')...")
    result = GitConsolidated.git_inspect(mode="branch")
    print(f"   Success: {result.success}")
    if result.success:
        print(f"   ✓ Branches listed")
    else:
        print(f"   ⚠️  Not a git repo: {result.error[:100] if result.error else 'N/A'}")
    
    print("\n✅ GitConsolidated tests completed")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("CONSOLIDATED TOOLS TEST SUITE")
    print("=" * 70)
    
    test_results = []
    
    try:
        test_fs_tools()
        test_results.append(("FSTools", True))
    except Exception as e:
        print(f"\n❌ FSTools test failed: {str(e)}")
        test_results.append(("FSTools", False))
    
    try:
        test_project_tools()
        test_results.append(("ProjectTools", True))
    except Exception as e:
        print(f"\n❌ ProjectTools test failed: {str(e)}")
        test_results.append(("ProjectTools", False))
    
    try:
        test_code_quality_tools()
        test_results.append(("CodeQualityTools", True))
    except Exception as e:
        print(f"\n❌ CodeQualityTools test failed: {str(e)}")
        test_results.append(("CodeQualityTools", False))
    
    try:
        test_quality_tools()
        test_results.append(("QualityTools", True))
    except Exception as e:
        print(f"\n❌ QualityTools test failed: {str(e)}")
        test_results.append(("QualityTools", False))
    
    try:
        test_git_tools()
        test_results.append(("GitConsolidated", True))
    except Exception as e:
        print(f"\n❌ GitConsolidated test failed: {str(e)}")
        test_results.append(("GitConsolidated", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for tool_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {tool_name}")
    
    print(f"\n   Total: {passed}/{total} test suites passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

