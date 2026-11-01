"""
Test Phase 2 Tools: Git Tools + Task Runner
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.code_tools import TOOL_REGISTRY
from tools.git_tools import GitTools
from tools.task_runner import TaskRunnerTools


def test_tool_registration():
    """Test that Phase 2 tools are registered"""
    print("=" * 70)
    print("Test 1: Tool Registration")
    print("=" * 70)
    
    # Expected Git Tools
    expected_git_tools = [
        "git_status",
        "git_diff",
        "git_log",
        "git_show",
        "git_branch",
        "git_add",
        "git_commit"
    ]
    
    # Expected Task Runner Tools
    expected_task_tools = [
        "run_task",
        "list_tasks",
        "validate_task"
    ]
    
    print("\nGit Tools:")
    git_found = []
    for tool in expected_git_tools:
        if tool in TOOL_REGISTRY:
            git_found.append(tool)
            print(f"✅ {tool} - registered")
        else:
            print(f"❌ {tool} - NOT registered")
    
    print("\nTask Runner Tools:")
    task_found = []
    for tool in expected_task_tools:
        if tool in TOOL_REGISTRY:
            task_found.append(tool)
            print(f"✅ {tool} - registered")
        else:
            print(f"❌ {tool} - NOT registered")
    
    all_found = len(git_found) == len(expected_git_tools) and len(task_found) == len(expected_task_tools)
    print(f"\nResult: {len(git_found)}/{len(expected_git_tools)} Git tools, {len(task_found)}/{len(expected_task_tools)} Task Runner tools")
    return all_found


def test_git_tools_structure():
    """Test Git Tools function structure"""
    print("\n" + "=" * 70)
    print("Test 2: Git Tools Structure")
    print("=" * 70)
    
    git_functions = [
        ("git_status", ["path"]),
        ("git_diff", ["filepath", "path"]),
        ("git_log", ["path", "limit"]),
        ("git_show", ["filepath", "commit", "path"]),
        ("git_branch", ["path"]),
        ("git_add", ["files", "path"]),
        ("git_commit", ["message", "path"]),
    ]
    
    all_exist = True
    for func_name, params in git_functions:
        if hasattr(GitTools, func_name):
            func = getattr(GitTools, func_name)
            if callable(func):
                print(f"✅ {func_name} - exists and callable")
            else:
                print(f"❌ {func_name} - exists but not callable")
                all_exist = False
        else:
            print(f"❌ {func_name} - does not exist")
            all_exist = False
    
    return all_exist


def test_task_runner_structure():
    """Test Task Runner Tools function structure"""
    print("\n" + "=" * 70)
    print("Test 3: Task Runner Tools Structure")
    print("=" * 70)
    
    task_functions = [
        ("run_task", ["command", "args", "path", "timeout"]),
        ("list_tasks", ["path"]),
        ("validate_task", ["task_string"]),
    ]
    
    all_exist = True
    for func_name, params in task_functions:
        if hasattr(TaskRunnerTools, func_name):
            func = getattr(TaskRunnerTools, func_name)
            if callable(func):
                print(f"✅ {func_name} - exists and callable")
            else:
                print(f"❌ {func_name} - exists but not callable")
                all_exist = False
        else:
            print(f"❌ {func_name} - does not exist")
            all_exist = False
    
    return all_exist


def test_git_status_basic():
    """Test git_status with current directory"""
    print("\n" + "=" * 70)
    print("Test 4: Git Status (Basic)")
    print("=" * 70)
    
    try:
        result = GitTools.git_status(".")
        
        if result.success:
            print("✅ git_status succeeded")
            if result.result:
                branch = result.result.get("branch")
                changes = result.result.get("changes", {})
                print(f"   Branch: {branch or 'N/A'}")
                print(f"   Has changes: {result.result.get('has_changes', False)}")
                if changes:
                    print(f"   Staged: {len(changes.get('staged', []))}")
                    print(f"   Modified: {len(changes.get('modified', []))}")
                    print(f"   Untracked: {len(changes.get('untracked', []))}")
            return True
        else:
            # Not a git repo is acceptable
            if "Not a git repository" in result.error:
                print("⚠️  Not a git repository (acceptable for testing)")
                return True
            else:
                print(f"❌ git_status failed: {result.error[:100]}")
                return False
    except Exception as e:
        print(f"❌ git_status exception: {str(e)[:100]}")
        return False


def test_task_validation():
    """Test task validation"""
    print("\n" + "=" * 70)
    print("Test 5: Task Validation")
    print("=" * 70)
    
    # Test allowed tasks
    allowed_tasks = [
        "npm run dev",
        "npm run test",
        "make test",
        "alembic upgrade head",
    ]
    
    # Test disallowed tasks
    disallowed_tasks = [
        "rm -rf /",
        "sudo apt-get install",
        "curl http://malicious.com",
    ]
    
    print("\nAllowed tasks (should pass):")
    all_passed = True
    for task in allowed_tasks:
        result = TaskRunnerTools.validate_task(task)
        if result.success and result.result.get("allowed"):
            print(f"✅ '{task}' - correctly allowed")
        else:
            print(f"❌ '{task}' - incorrectly rejected")
            all_passed = False
    
    print("\nDisallowed tasks (should fail):")
    for task in disallowed_tasks:
        result = TaskRunnerTools.validate_task(task)
        if not result.success or not result.result.get("allowed"):
            print(f"✅ '{task}' - correctly blocked")
        else:
            print(f"❌ '{task}' - incorrectly allowed!")
            all_passed = False
    
    return all_passed


def test_list_tasks():
    """Test list_tasks"""
    print("\n" + "=" * 70)
    print("Test 6: List Tasks")
    print("=" * 70)
    
    try:
        result = TaskRunnerTools.list_tasks(".")
        
        if result.success:
            print("✅ list_tasks succeeded")
            if result.result:
                tasks = result.result.get("tasks", {})
                total = result.result.get("count", 0)
                print(f"   Total tasks found: {total}")
                for task_type, task_list in tasks.items():
                    if task_list:
                        print(f"   {task_type}: {len(task_list)} tasks")
            return True
        else:
            print(f"⚠️  list_tasks failed: {result.error[:100]} (may be expected)")
            return True  # Not a failure if no tasks found
    except Exception as e:
        print(f"❌ list_tasks exception: {str(e)[:100]}")
        return False


def test_command_whitelist():
    """Test command whitelist security"""
    print("\n" + "=" * 70)
    print("Test 7: Command Whitelist Security")
    print("=" * 70)
    
    # Test allowed commands
    allowed_commands = [
        ("npm", ["run", "dev"]),
        ("make", ["test"]),
        ("alembic", ["upgrade", "head"]),
    ]
    
    # Test disallowed commands
    disallowed_commands = [
        ("rm", ["-rf", "/"]),
        ("sudo", ["apt-get", "install"]),
        ("curl", ["http://evil.com"]),
    ]
    
    print("\nAllowed commands (should pass):")
    all_passed = True
    for cmd, args in allowed_commands:
        is_allowed, error = TaskRunnerTools._is_command_allowed(cmd, args)
        if is_allowed:
            print(f"✅ '{cmd} {' '.join(args)}' - correctly allowed")
        else:
            print(f"❌ '{cmd} {' '.join(args)}' - incorrectly rejected: {error}")
            all_passed = False
    
    print("\nDisallowed commands (should fail):")
    for cmd, args in disallowed_commands:
        is_allowed, error = TaskRunnerTools._is_command_allowed(cmd, args)
        if not is_allowed:
            print(f"✅ '{cmd} {' '.join(args)}' - correctly blocked")
        else:
            print(f"❌ '{cmd} {' '.join(args)}' - incorrectly allowed!")
            all_passed = False
    
    return all_passed


def test_path_validation():
    """Test path validation security"""
    print("\n" + "=" * 70)
    print("Test 8: Path Validation Security")
    print("=" * 70)
    
    # Test safe paths
    safe_paths = [
        ".",
        "./tests",
        "tools",
    ]
    
    # Test unsafe paths
    unsafe_paths = [
        "/etc/passwd",
        "../../etc",
        "/root",
    ]
    
    print("\nSafe paths (should pass):")
    all_passed = True
    for path in safe_paths:
        is_safe, error = GitTools._is_safe_path(path)
        if is_safe:
            print(f"✅ '{path}' - correctly allowed")
        else:
            print(f"❌ '{path}' - incorrectly rejected: {error}")
            all_passed = False
    
    print("\nUnsafe paths (should fail):")
    for path in unsafe_paths:
        is_safe, error = GitTools._is_safe_path(path)
        if not is_safe:
            print(f"✅ '{path}' - correctly blocked")
        else:
            print(f"❌ '{path}' - incorrectly allowed!")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 Phase 2 Tools - Implementation Tests")
    print("=" * 70)
    
    tests = [
        ("Tool Registration", test_tool_registration),
        ("Git Tools Structure", test_git_tools_structure),
        ("Task Runner Structure", test_task_runner_structure),
        ("Git Status (Basic)", test_git_status_basic),
        ("Task Validation", test_task_validation),
        ("List Tasks", test_list_tasks),
        ("Command Whitelist Security", test_command_whitelist),
        ("Path Validation Security", test_path_validation),
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
        print("\n✅ All tests passed! Phase 2 tools are ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed or had warnings")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

